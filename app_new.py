from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
import requests
import os
import io
from PIL import Image
import base64

app = FastAPI()
os.makedirs("temp", exist_ok=True)

# ВСТАВЬТЕ ВАШ КЛЮЧ ОТ PHOTOROOM
PHOTOROOM_API_KEY = "sandbox_sk_pr_default_7a0dddbd117eb81cda4214abab36da97ff8cafb0"

def remove_background(image_bytes):
    files = {'image_file': ('photo.jpg', image_bytes, 'image/jpeg')}
    headers = {'x-api-key': PHOTOROOM_API_KEY}
    data = {'format': 'png'}
    
    response = requests.post(
        'https://sdk.photoroom.com/v1/segment',
        headers=headers,
        files=files,
        data=data,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Ошибка удаления фона: {response.status_code}")
    
    return response.content

def add_background(foreground_bytes, bg_type, bg_color=None, bg_image_bytes=None, gradient_colors=None):
    fg = Image.open(io.BytesIO(foreground_bytes)).convert("RGBA")
    
    if bg_type == "color" and bg_color:
        bg = Image.new("RGBA", fg.size, bg_color)
        bg.paste(fg, (0, 0), fg)
        return bg
    
    elif bg_type == "image" and bg_image_bytes:
        bg = Image.open(io.BytesIO(bg_image_bytes)).convert("RGBA")
        bg = bg.resize(fg.size, Image.Resampling.LANCZOS)
        bg.paste(fg, (0, 0), fg)
        return bg
    
    elif bg_type == "gradient" and gradient_colors:
        bg = Image.new("RGBA", fg.size)
        width, height = fg.size
        colors = gradient_colors.split(',')
        if len(colors) >= 2:
            color1 = colors[0].strip()
            color2 = colors[1].strip()
        else:
            color1 = "#6366f1"
            color2 = "#8b5cf6"
        
        for y in range(height):
            ratio = y / height
            r = int(int(color1[1:3], 16) * (1 - ratio) + int(color2[1:3], 16) * ratio)
            g = int(int(color1[3:5], 16) * (1 - ratio) + int(color2[3:5], 16) * ratio)
            b = int(int(color1[5:7], 16) * (1 - ratio) + int(color2[5:7], 16) * ratio)
            for x in range(width):
                bg.putpixel((x, y), (r, g, b, 255))
        
        bg.paste(fg, (0, 0), fg)
        return bg
    
    else:
        return fg

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
        <title>AI Фотостудия — Замени фон</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                padding: 16px;
            }
            .container {
                background: rgba(255,255,255,0.07);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                padding: 24px 20px;
                max-width: 700px;
                width: 100%;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6);
                border: 1px solid rgba(255,255,255,0.08);
            }
            h1 {
                font-size: 24px;
                font-weight: 700;
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 6px;
                text-align: center;
                flex-wrap: wrap;
            }
            .subtitle {
                color: rgba(255,255,255,0.6);
                text-align: center;
                font-size: 14px;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.06);
                padding-bottom: 16px;
            }
            .form-group {
                margin-bottom: 14px;
            }
            .form-group label {
                display: block;
                color: rgba(255,255,255,0.8);
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 5px;
            }
            .upload-box {
                background: rgba(255,255,255,0.04);
                border: 2px dashed rgba(255,255,255,0.15);
                border-radius: 14px;
                padding: 16px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .upload-box:hover {
                border-color: rgba(255,255,255,0.3);
                background: rgba(255,255,255,0.07);
            }
            .upload-box input[type="file"] {
                display: none;
            }
            .upload-label {
                display: inline-block;
                background: rgba(255,255,255,0.08);
                color: #fff;
                padding: 8px 18px;
                border-radius: 60px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s ease;
                border: 1px solid rgba(255,255,255,0.06);
            }
            .upload-label:hover {
                background: rgba(255,255,255,0.14);
            }
            .file-name {
                color: rgba(255,255,255,0.4);
                font-size: 12px;
                margin-top: 5px;
            }
            select, input[type="text"] {
                width: 100%;
                padding: 10px 14px;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05);
                color: #fff;
                font-size: 13px;
                outline: none;
                transition: all 0.2s ease;
                font-family: 'Inter', sans-serif;
                -webkit-appearance: none;
                appearance: none;
            }
            select:focus, input[type="text"]:focus {
                border-color: rgba(139, 92, 246, 0.5);
                background: rgba(255,255,255,0.08);
            }
            select option {
                background: #1a1a2e;
                color: #fff;
            }
            .btn-primary {
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: #fff;
                border: none;
                padding: 14px 20px;
                border-radius: 60px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
                box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.4);
                touch-action: manipulation;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 28px -8px rgba(99, 102, 241, 0.6);
            }
            .btn-primary:active {
                transform: scale(0.97);
            }
            .btn-group {
                display: flex;
                gap: 10px;
                margin-top: 14px;
                flex-wrap: wrap;
                justify-content: center;
            }
            .btn-download {
                background: linear-gradient(135deg, #10b981, #059669);
                color: #fff;
                border: none;
                padding: 12px 20px;
                border-radius: 60px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                flex: 1;
                min-width: 120px;
                box-shadow: 0 6px 16px -4px rgba(16, 185, 129, 0.35);
                touch-action: manipulation;
            }
            .btn-download:hover {
                transform: translateY(-2px);
            }
            .btn-reset {
                background: rgba(255,255,255,0.08);
                color: #fff;
                border: 1px solid rgba(255,255,255,0.1);
                padding: 12px 20px;
                border-radius: 60px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                flex: 1;
                min-width: 120px;
                touch-action: manipulation;
            }
            .btn-reset:hover {
                background: rgba(255,255,255,0.15);
                transform: translateY(-2px);
            }
            .bg-options {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .bg-options label {
                display: flex;
                align-items: center;
                gap: 5px;
                color: rgba(255,255,255,0.7);
                font-size: 13px;
                cursor: pointer;
                padding: 4px 0;
            }
            .bg-options input[type="radio"] {
                accent-color: #8b5cf6;
                width: 16px;
                height: 16px;
                cursor: pointer;
                flex-shrink: 0;
            }
            .hidden {
                display: none !important;
            }

            /* ===== РЕЗУЛЬТАТ СРАВНЕНИЯ ===== */
            .compare-wrapper {
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 16px;
            }
            .compare-item {
                flex: 1 1 200px;
                min-width: 150px;
                max-width: 100%;
                background: rgba(0,0,0,0.25);
                border-radius: 16px;
                padding: 12px;
                border: 1px solid rgba(255,255,255,0.06);
            }
            .compare-item img {
                width: 100%;
                height: auto;
                max-height: 300px;
                object-fit: contain;
                border-radius: 10px;
                background: rgba(0,0,0,0.3);
                display: block;
            }
            .compare-label {
                color: rgba(255,255,255,0.6);
                font-size: 12px;
                text-align: center;
                margin-top: 6px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }
            .badge-original {
                color: #fcd34d;
            }
            .badge-result {
                color: #6ee7b7;
            }

            /* ===== СПИННЕР ===== */
            .spinner {
                border: 3px solid rgba(255,255,255,0.08);
                border-top: 3px solid #8b5cf6;
                border-radius: 50%;
                width: 44px;
                height: 44px;
                animation: spin 0.9s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .status-text {
                color: rgba(255,255,255,0.7);
                font-size: 14px;
                text-align: center;
                margin-top: 6px;
            }
            .error-text {
                color: #fca5a5;
                background: rgba(220, 38, 38, 0.15);
                padding: 12px 16px;
                border-radius: 12px;
                border: 1px solid rgba(220, 38, 38, 0.2);
                font-size: 14px;
                text-align: center;
            }

            /* ===== АДАПТАЦИЯ ПОД ТЕЛЕФОН ===== */
            @media (max-width: 480px) {
                .container {
                    padding: 16px 12px;
                    border-radius: 16px;
                }
                h1 {
                    font-size: 20px;
                    gap: 6px;
                }
                .subtitle {
                    font-size: 12px;
                    margin-bottom: 14px;
                    padding-bottom: 12px;
                }
                .upload-box {
                    padding: 12px;
                }
                .btn-primary {
                    padding: 14px 16px;
                    font-size: 15px;
                }
                .btn-download, .btn-reset {
                    padding: 12px 16px;
                    font-size: 13px;
                    min-width: 100%;
                }
                .btn-group {
                    flex-direction: column;
                    gap: 8px;
                }
                .compare-wrapper {
                    flex-direction: column;
                    gap: 12px;
                }
                .compare-item {
                    flex: 1 1 auto;
                    min-width: unset;
                }
                .compare-item img {
                    max-height: 220px;
                }
                .bg-options {
                    gap: 6px;
                }
                .bg-options label {
                    font-size: 12px;
                }
                select, input[type="text"] {
                    font-size: 14px;
                    padding: 12px 14px;
                }
                .form-group {
                    margin-bottom: 12px;
                }
                .form-group label {
                    font-size: 12px;
                }
                .upload-label {
                    font-size: 12px;
                    padding: 6px 16px;
                }
            }

            @media (max-width: 380px) {
                .container {
                    padding: 12px 8px;
                }
                h1 {
                    font-size: 17px;
                }
                .compare-item img {
                    max-height: 160px;
                }
                .btn-primary {
                    font-size: 14px;
                    padding: 12px 12px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Замени фон за секунду</h1>
            <p class="subtitle">Удаляем старый фон и ставим новый — цвет, картинку или градиент</p>

            <div class="form-group">
                <label>📷 Фото с человеком</label>
                <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" accept="image/*">
                    <span class="upload-label">Выбрать фото</span>
                    <div id="fileName" class="file-name">Файл не выбран</div>
                </div>
            </div>

            <div class="form-group">
                <label>🎨 Тип фона</label>
                <div class="bg-options">
                    <label><input type="radio" name="bg_type" value="color" checked onchange="toggleBgOptions()"> 🎨 Цвет</label>
                    <label><input type="radio" name="bg_type" value="image" onchange="toggleBgOptions()"> 🖼️ Картинка</label>
                    <label><input type="radio" name="bg_type" value="gradient" onchange="toggleBgOptions()"> 🌈 Градиент</label>
                </div>
            </div>

            <!-- Выбор цвета -->
            <div class="form-group" id="colorOptions">
                <label>Выберите цвет фона</label>
                <select id="bgColor">
                    <option value="#ffffff">⬜ Белый</option>
                    <option value="#e0f2fe">🟦 Голубой</option>
                    <option value="#d1fae5">🟩 Зелёный</option>
                    <option value="#fce4ec">🟪 Светло-розовый</option>
                    <option value="#fef3c7">🟨 Жёлтый</option>
                    <option value="#1a1a2e">⬛ Тёмный</option>
                    <option value="#f472b6">💗 Насыщенный розовый</option>
                    <option value="#fb923c">🟧 Оранжевый</option>
                    <option value="#a78bfa">🟪 Фиолетовый</option>
                    <option value="#ef4444">🔴 Красный</option>
                </select>
            </div>

            <!-- Загрузка своей картинки -->
            <div class="form-group hidden" id="imageOptions">
                <label>🖼️ Загрузите картинку для фона</label>
                <div class="upload-box" onclick="document.getElementById('bgFileInput').click()">
                    <input type="file" id="bgFileInput" accept="image/*">
                    <span class="upload-label">Выбрать фон</span>
                    <div id="bgFileName" class="file-name">Файл не выбран</div>
                </div>
            </div>

            <!-- Градиент -->
            <div class="form-group hidden" id="gradientOptions">
                <label>🌈 Цвета градиента (два цвета через запятую)</label>
                <input type="text" id="gradientColors" value="#6366f1, #8b5cf6" placeholder="например: #ff6b6b, #4ecdc4">
                <div style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap;">
                    <button type="button" class="upload-label" onclick="setGradient('#6366f1,#8b5cf6')">Фиолетовый</button>
                    <button type="button" class="upload-label" onclick="setGradient('#f093fb,#f5576c')">Розовый</button>
                    <button type="button" class="upload-label" onclick="setGradient('#4facfe,#00f2fe')">Голубой</button>
                    <button type="button" class="upload-label" onclick="setGradient('#43e97b,#38f9d7')">Зелёный</button>
                    <button type="button" class="upload-label" onclick="setGradient('#fa709a,#fee140')">Закат</button>
                </div>
            </div>

            <button class="btn-primary" onclick="sendImage()">🚀 Обработать фото</button>

            <div id="result">
                <p style="color: rgba(255,255,255,0.3); text-align: center; padding: 30px 0; font-size: 13px;">
                    Результат появится здесь
                </p>
            </div>
        </div>

        <script>
            let currentResultBlob = null;
            let originalImageUrl = null;

            document.getElementById('fileInput').addEventListener('change', function(e) {
                const file = e.target.files[0];
                document.getElementById('fileName').textContent = file ? file.name : 'Файл не выбран';
                if (file) {
                    originalImageUrl = URL.createObjectURL(file);
                }
            });

            document.getElementById('bgFileInput').addEventListener('change', function(e) {
                document.getElementById('bgFileName').textContent = e.target.files[0]?.name || 'Файл не выбран';
            });

            function toggleBgOptions() {
                const bgType = document.querySelector('input[name="bg_type"]:checked').value;
                document.getElementById('colorOptions').classList.toggle('hidden', bgType !== 'color');
                document.getElementById('imageOptions').classList.toggle('hidden', bgType !== 'image');
                document.getElementById('gradientOptions').classList.toggle('hidden', bgType !== 'gradient');
            }

            function setGradient(colors) {
                document.getElementById('gradientColors').value = colors;
            }

            async function sendImage() {
                const fileInput = document.getElementById('fileInput');
                const file = fileInput.files[0];
                if (!file) {
                    alert('📸 Сначала выберите фото!');
                    return;
                }

                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `
                    <div class="spinner"></div>
                    <p class="status-text">⏳ ИИ обрабатывает фото... это займёт до 30 секунд</p>
                `;

                const formData = new FormData();
                formData.append('file', file);

                const bgType = document.querySelector('input[name="bg_type"]:checked').value;
                formData.append('bg_type', bgType);

                if (bgType === 'color') {
                    formData.append('bg_color', document.getElementById('bgColor').value);
                } else if (bgType === 'image') {
                    const bgFile = document.getElementById('bgFileInput').files[0];
                    if (bgFile) {
                        formData.append('bg_image', bgFile);
                    } else {
                        resultDiv.innerHTML = `<p class="error-text">❌ Выберите картинку для фона!</p>`;
                        return;
                    }
                } else if (bgType === 'gradient') {
                    formData.append('gradient_colors', document.getElementById('gradientColors').value);
                }

                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Ошибка ${response.status}: ${errorText}`);
                    }

                    const blob = await response.blob();
                    currentResultBlob = blob;
                    const resultUrl = URL.createObjectURL(blob);

                    // === ПОКАЗЫВАЕМ ДО/ПОСЛЕ ===
                    const originalHtml = originalImageUrl 
                        ? `<div class="compare-item">
                            <img src="${originalImageUrl}" alt="Исходное фото" />
                            <div class="compare-label badge-original">📷 Исходное</div>
                        </div>`
                        : '';

                    resultDiv.innerHTML = `
                        <div class="compare-wrapper">
                            ${originalHtml}
                            <div class="compare-item">
                                <img src="${resultUrl}" alt="Результат" />
                                <div class="compare-label badge-result">✨ Результат</div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="btn-download" onclick="downloadResult()">⬇️ Скачать PNG</button>
                            <button class="btn-reset" onclick="resetApp()">🔄 Новое фото</button>
                        </div>
                    `;
                } catch (error) {
                    resultDiv.innerHTML = `<p class="error-text">❌ ${error.message}</p>`;
                    console.error('Ошибка:', error);
                }
            }

            function downloadResult() {
                if (!currentResultBlob) {
                    alert('Нет результата для скачивания!');
                    return;
                }
                const link = document.createElement('a');
                link.href = URL.createObjectURL(currentResultBlob);
                link.download = 'result_with_bg.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            function resetApp() {
                document.getElementById('result').innerHTML = `
                    <p style="color: rgba(255,255,255,0.3); text-align: center; padding: 30px 0; font-size: 13px;">
                        Результат появится здесь
                    </p>
                `;
                document.getElementById('fileInput').value = '';
                document.getElementById('fileName').textContent = 'Файл не выбран';
                document.getElementById('bgFileInput').value = '';
                document.getElementById('bgFileName').textContent = 'Файл не выбран';
                currentResultBlob = null;
                originalImageUrl = null;
            }
        </script>
    </body>
    </html>
    """

@app.post("/process")
async def process(
    file: UploadFile = File(...),
    bg_type: str = Form("color"),
    bg_color: str = Form(None),
    bg_image: UploadFile = File(None),
    gradient_colors: str = Form(None)
):
    image_data = await file.read()
    foreground_bytes = remove_background(image_data)
    
    bg_image_bytes = None
    if bg_image and bg_image.filename:
        bg_image_bytes = await bg_image.read()
    
    result_image = add_background(
        foreground_bytes, 
        bg_type, 
        bg_color, 
        bg_image_bytes,
        gradient_colors
    )
    
    file_path = "temp/result.png"
    result_image.save(file_path, "PNG")
    
    return FileResponse(file_path, media_type="image/png")

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
