import { argon2id } from "https://esm.sh/@noble/hashes/argon2";

const phraseInput = document.querySelector("#seedPhrase");
const phraseSubmit = document.querySelector("#seedSubmit");

function toBase64(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

function fromBase64(b64) {
    return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

const userKeyData = await fetch("/api/user/key/", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    }
}).then(async response => await response.json());

phraseSubmit.onclick = async function() {
    const phrase = phraseInput.value;
    const encryptedPrivateKey = fromBase64(userKeyData.privateKey);
    const publicKey = fromBase64(userKeyData.publicKey);
    const salt = fromBase64(userKeyData.salt);
    const iv = fromBase64(userKeyData.iv);

    const encoder = new TextEncoder();
    const phraseBytes = encoder.encode(phrase);

    const keyMaterial = argon2id(phraseBytes, salt, {
        t: 3,
        m: 65536,
        p: 1,
        dkLen: 32
    });

    const aesKey = await crypto.subtle.importKey(
        "raw",
        keyMaterial,
        {name: "AES-GCM"},
        false,
        ["encrypt", "decrypt"]
    );

    const decryptedPrivateKey = await crypto.subtle.decrypt(
        {name: "AES-GCM", iv: iv},
        aesKey,
        encryptedPrivateKey
    );

    const idDB = indexedDB.open("secure-storage", 3);

    idDB.onupgradeneeded = () => {
        const db = idDB.result;
        if (!db.objectStoreNames.contains("vault")) {
            db.createObjectStore("vault"); // создаём объектное хранилище
        }
    }

    idDB.onsuccess = () => {
        const db = idDB.result;
        const tx = db.transaction("vault", "readwrite");
        const store = tx.objectStore("vault");

        store.put({
            privateKey: toBase64(decryptedPrivateKey),
            publicKey: toBase64(publicKey),
            salt: toBase64(salt),
            iv: toBase64(iv),
            phrase: toBase64(phraseBytes)
        }, "main");

        document.location.href = "/me/";
    };
}