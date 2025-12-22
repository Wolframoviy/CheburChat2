import { argon2id } from "https://esm.sh/@noble/hashes/argon2";

const user2_id = document.querySelector("#userId").value;

function toBase64(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

function fromBase64(b64) {
    return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

const randKey = crypto.getRandomValues(new Uint8Array(16));
const salt = crypto.getRandomValues(new Uint8Array(16));


const keyMaterial = argon2id(randKey, salt, {
    t: 3,
    m: 65536,
    p: 1,
    dkLen: 32
});

const aesKey = await crypto.subtle.importKey(
        "raw",
        keyMaterial,
        {name: "AES-GCM"},
        true,
        ["encrypt", "decrypt"]
    );

await fetch("/api/user/public/" + user2_id).then(response => response.json()).then(async response => {
    const user2publicKey = await crypto.subtle.importKey(
        "spki",
        fromBase64(response.publicKey),
        {
            name: "RSA-OAEP",
            hash: "SHA-256"
        },
        true,
        ["encrypt"]
    );
    const iDB = indexedDB.open("secure-storage");

    iDB.onsuccess = () => {
        const db = iDB.result;

        const tx = db.transaction("vault", "readonly");
        const store = tx.objectStore("vault");

        const res = store.get("main");

        res.onsuccess = async () => {
            const user1publicKey = await crypto.subtle.importKey(
                "spki",
                fromBase64(res.result.publicKey),
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["encrypt"]
            );
            const encrypted1AES = await crypto.subtle.encrypt(
                {
                    name: "RSA-OAEP",
                     hash: "SHA-256"
                },
                user1publicKey,
                await crypto.subtle.exportKey(
                    "raw",
                    aesKey
                )
            );
            const encrypted2AES = await crypto.subtle.encrypt(
                {name: "RSA-OAEP"},
                user2publicKey,
                await crypto.subtle.exportKey(
                    "raw",
                    aesKey
                )
            );

            const payload = {
                user1aes: toBase64(encrypted1AES),
                user2aes: toBase64(encrypted2AES),
                user2_id: user2_id
            };


            await fetch("/start/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }).then(response => {
                if (response.status === 200)   {
                    document.location.href = "/chats/";
                } else {
                    console.log(response.status);
                }
            });
        }
    };
})