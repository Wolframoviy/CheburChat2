import { argon2id } from "https://esm.sh/@noble/hashes/argon2";

const phraseInput = document.querySelector("#seedPhrase");
const phraseSubmit = document.querySelector("#seedSubmit");

const keyPair = await crypto.subtle.generateKey(
        {
            name: "RSA-OAEP",
            modulusLength: 2048,          // 2048 минимум, можно 3072
            publicExponent: new Uint8Array([1, 0, 1]), // 65537
            hash: "SHA-256"
        },
        true,
        ["encrypt", "decrypt"]
    );

const publicKey = await crypto.subtle.exportKey(
    "spki",
    keyPair.publicKey
);

function toBase64(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

function fromBase64(b64) {
    return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

phraseSubmit.onclick = async function () {
    const phrase = phraseInput.value;

    const encoder = new TextEncoder();
    const phraseBytes = encoder.encode(phrase);

    const salt = crypto.getRandomValues(new Uint8Array(16));

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

    const iv = crypto.getRandomValues(new Uint8Array(12));

    const encryptedPrivate = await crypto.subtle.encrypt(
        {name: "AES-GCM", iv},
        aesKey,
        await crypto.subtle.exportKey(
            "pkcs8",
            keyPair.privateKey
        )
    );

    const payload = {
        publicKey: toBase64(publicKey),
        privateKey: toBase64(encryptedPrivate),
        salt: toBase64(salt),
        iv: toBase64(iv)
    };

    await fetch("/generate/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    await crypto.subtle.exportKey(
                "pkcs8",
                keyPair.privateKey
            ).then(privateKey => {
    const idDB = indexedDB.open("secure-storage", 3);

    idDB.onupgradeneeded = () => {
        const db = idDB.result;
        if (!db.objectStoreNames.contains("vault")) {
            db.createObjectStore("vault"); // создаём объектное хранилище
        }
    }

    idDB.onsuccess = async () => {
        const db = idDB.result;
        const tx = db.transaction("vault", "readwrite");
        const store = tx.objectStore("vault");


        store.put({
            privateKey: toBase64(privateKey),
            publicKey: toBase64(publicKey),
            salt: toBase64(salt),
            iv: toBase64(iv),
            phrase: toBase64(phraseBytes)
        }, "main");
        };

        document.location.href = "/me/";
    });


};

// document.addEventListener("DOMContentLoaded", async function () {
//
// });
