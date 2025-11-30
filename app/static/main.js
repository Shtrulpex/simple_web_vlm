// app/static/main.js

let vqaSessionId = null;

function showError(msg) {
    document.getElementById("error").textContent = msg;
}

document.addEventListener("DOMContentLoaded", () => {
    // VQA init
    const vqaInitForm = document.getElementById("vqa-init-form");
    const vqaAskForm = document.getElementById("vqa-ask-form");

    vqaInitForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        showError("");

        const fileInput = document.getElementById("vqa-image");
        if (!fileInput.files[0]) {
            showError("Пожалуйста, выберите изображение.");
            return;
        }

        const file = fileInput.files[0];
        if (!file.type.startsWith("image/")) {
            showError("Неверный тип файла. Загрузите изображение.");
            return;
        }

        const formData = new FormData();
        formData.append("image", file);

        try {
            const resp = await fetch("/api/vqa/init", {
                method: "POST",
                body: formData,
            });
            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "Ошибка сервера");
            }
            const data = await resp.json();
            vqaSessionId = data.session_id;
            document.getElementById("vqa-caption").textContent = "Описание: " + data.caption;
            vqaAskForm.style.display = "block";
        } catch (err) {
            showError(err.message);
        }
    });

    // VQA ask
    vqaAskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        showError("");
        if (!vqaSessionId) {
            showError("Сначала загрузите изображение.");
            return;
        }

        const question = document.getElementById("vqa-question").value.trim();
        if (!question) {
            showError("Введите вопрос.");
            return;
        }

        const formData = new FormData();
        formData.append("session_id", vqaSessionId);
        formData.append("question", question);

        try {
            const resp = await fetch("/api/vqa/ask", {
                method: "POST",
                body: formData,
            });
            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "Ошибка сервера");
            }
            const data = await resp.json();
            document.getElementById("vqa-answer").textContent = "Ответ: " + data.answer;
        } catch (err) {
            showError(err.message);
        }
    });

    // OCR
    const ocrForm = document.getElementById("ocr-form");
    ocrForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        showError("");

        const fileInput = document.getElementById("ocr-image");
        const maxLengthInput = document.getElementById("ocr-max-length");

        if (!fileInput.files[0]) {
            showError("Пожалуйста, выберите изображение для OCR.");
            return;
        }

        const file = fileInput.files[0];
        if (!file.type.startsWith("image/")) {
            showError("Неверный тип файла. Загрузите изображение.");
            return;
        }

        const maxLen = parseInt(maxLengthInput.value, 10);
        if (isNaN(maxLen) || maxLen <= 0 || maxLen > 2048) {
            showError("max_length должен быть числом от 1 до 2048.");
            return;
        }

        const formData = new FormData();
        formData.append("image", file);
        formData.append("max_length", maxLen);

        try {
            const resp = await fetch("/api/ocr", {
                method: "POST",
                body: formData,
            });
            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "Ошибка сервера");
            }
            const data = await resp.json();
            document.getElementById("ocr-text").textContent = data.text;
            const link = document.getElementById("ocr-download-link");
            link.href = `/api/ocr/${data.ocr_id}/download`;
            link.style.display = "inline";
        } catch (err) {
            showError(err.message);
        }
    });
});
