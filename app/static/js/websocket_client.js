function toBase64(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

function fromBase64(b64) {
    return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

const iDB = indexedDB.open("secure-storage");

let chatKey;

iDB.onsuccess = () => {
    const db = iDB.result;

    const tx = db.transaction("vault", "readonly");
    const store = tx.objectStore("vault");

    const res = store.get("main");

    res.onsuccess = async () => {
        const privateKey = await crypto.subtle.importKey(
            "pkcs8",
            fromBase64(res.result.privateKey),
            {
                name: "RSA-OAEP",
                hash: "SHA-256"
            },
            true,
            ["decrypt"]
        );
        fetch("/api/chats/aes/" + document.chat_id, {
            method: "GET"
        }).then(response => response.json()).then(async response => {
            const rawAes = await crypto.subtle.decrypt(
                {name: "RSA-OAEP"},
                privateKey,
                fromBase64(response.aes)
            );
            chatKey = await crypto.subtle.importKey(
                "raw",
                rawAes,
                {name: "AES-GCM"},
                false,
                ["decrypt", "encrypt"]
            );
        });
    };
};

async function decryptMessage(data, iv) {
    const decoder = new TextDecoder("UTF-8");

    return await crypto.subtle.decrypt(
        {name: "AES-GCM", iv: iv},
        chatKey,
        data
    ).then(res => decoder.decode(res));
}


document.addEventListener("DOMContentLoaded", function(){

    const messagesContainer = document.querySelector("#messages_container");
    const messageInput = document.querySelector("[name=message_input]");
    const sendMessageButton = document.querySelector("[name=send_message_button]");

    let loading = true;
    let end = false;
    let last_message = -1;

    function addMessage(author, message, pre=false) {
        const newMessage = document.createElement("div");
        const newMessageImage = document.createElement("img");
        const newMessageBubble = document.createElement("div");
        const newMessageText = document.createElement("div");
        const newMessageUsername = document.createElement("div");
        newMessage.classList.add("message");
        newMessageImage.classList.add("object-fit-scale");
        newMessageImage.classList.add("message-avatar");
        newMessageBubble.classList.add("message-bubble");
        newMessageUsername.classList.add("message-username");
        newMessageText.classList.add("message-text");
        newMessageImage.src = "/static/images/maxwell-cat.gif"
        newMessageUsername.textContent = author;
        newMessageText.innerText = message;
        newMessageBubble.appendChild(newMessageUsername);
        newMessageBubble.appendChild(newMessageText);
        newMessage.appendChild(newMessageImage);
        newMessage.appendChild(newMessageBubble);
        if(!pre) {
            messagesContainer.appendChild(newMessage);
        } else {
            messagesContainer.prepend(newMessage);
        }
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    const socket = io();

    socket.emit("status.update", {
        chat_id: document.chat_id
    });

    function loadHistory() {
        socket.emit("message.loadHistory", {
            chat_id: document.chat_id,
            from: last_message
        });
    }

    loadHistory()

    sendMessageButton.onclick = async function() {
        if (messageInput.value === "") {
            return;
        }

        const encoder = new TextEncoder();
        const data = encoder.encode(messageInput.value);
        messageInput.value = "";

        const iv = crypto.getRandomValues(new Uint8Array(12));

        const encryptedMessage = await crypto.subtle.encrypt(
            {name: "AES-GCM", iv},
            chatKey,
            data
        );

        const payload = {
            chat_id: document.chat_id,
            data: toBase64(encryptedMessage),
            iv: toBase64(iv)
        };

        socket.emit("message.send", payload);
    }

    socket.on("message.ack", (socket) => console.log("ACK"));

    socket.on("message.new", async (data) => {
        const author = data.author;
        const timestamp = data.timestamp;
        const encryptedData = fromBase64(data.data);
        const iv = fromBase64(data.iv);

        decryptMessage(encryptedData, iv).then(message => addMessage(author, message));
    });

    socket.on("message.history", (data) => {
        data.messages.forEach(messageData => decryptMessage(fromBase64(messageData.data), fromBase64(messageData.iv)).then(message => addMessage(messageData.author, message, true)));
        last_message = data.last;
        end = data.end;
        loading = false;
    })

    messagesContainer.addEventListener("scroll", function() {
            if (messagesContainer.scrollTop < 50 && !loading && !end) {
                loading = true;
                loadHistory(last_message);
            }
        });
})