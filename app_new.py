from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
import requests
import os
import io
import base64
from PIL import Image, ImageFilter, ImageEnhance

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

def upscale_image(image_bytes, scale=2):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    new_size = (img.width * scale, img.height * scale)
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Фотостудия — Замени фон</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap" rel="stylesheet">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
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
                max-width: 750px;
                width: 100%;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6);
                border: 1px solid rgba(255,255,255,0.08);
            }
            .logo {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 8px;
            }
            .logo-icon {
                font-size: 28px;
                animation: pulse 2s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            .logo-text {
                font-size: 24px;
                font-weight: 700;
                background: linear-gradient(135deg, #a78bfa, #f472b6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle {
                color: rgba(255,255,255,0.6);
                text-align: center;
                font-size: 14px;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.06);
                padding-bottom: 16px;
            }
            .form-group { margin-bottom: 14px; }
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
            .upload-box input[type="file"] { display: none; }
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
            .upload-label:hover { background: rgba(255,255,255,0.14); }
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
                font-family: 'Inter', sans-serif;
            }
            select option { background: #1a1a2e; color: #fff; }
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
            }
            .btn-primary:hover {
                transform: translateY(-2px);
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
                flex: 1;
                min-width: 120px;
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
                flex: 1;
                min-width: 120px;
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
            }
            .bg-options input[type="radio"] {
                accent-color: #8b5cf6;
                width: 16px;
                height: 16px;
            }
            .hidden { display: none !important; }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 8px;
                margin: 10px 0;
                padding: 10px;
                background: rgba(255,255,255,0.03);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.06);
            }
            .checkbox-group input[type="checkbox"] {
                accent-color: #10b981;
                width: 18px;
                height: 18px;
                cursor: pointer;
            }
            .checkbox-group label {
                color: rgba(255,255,255,0.8);
                font-size: 13px;
                cursor: pointer;
                margin: 0;
            }
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
            }
            .badge-original { color: #fcd34d; }
            .badge-result { color: #6ee7b7; }
            .spinner {
                border: 3px solid rgba(255,255,255,0.08);
                border-top: 3px solid #8b5cf6;
                border-radius: 50%;
                width: 44px;
                height: 44px;
                animation: spin 0.9s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin { to { transform: rotate(360deg); } }
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
            @media (max-width: 480px) {
                .container { padding: 16px 12px; border-radius: 16px; }
                .logo-text { font-size: 20px; }
                .logo-icon { font-size: 24px; }
                .btn-primary { padding: 14px 16px; font-size: 15px; }
                .btn-download, .btn-reset {
                    padding: 12px 16px;
                    font-size: 13px;
                    min-width: 100%;
                }
                .btn-group { flex-direction: column; gap: 8px; }
                .compare-wrapper { flex-direction: column; gap: 12px; }
                .compare-item { flex: 1 1 auto; min-width: unset; }
                .compare-item img { max-height: 220px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <span class="logo-icon">✨</span>
                <span class="logo-text">AI Фотостудия</span>
            </div>
            <p class="subtitle">Удаляем фон и ставим новый — цвет, картинку или градиент</p>

            <div class="form-group">
                <label>📷 Фото (можно выбрать несколько)</label>
                <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" accept="image/*" multiple>
                    <span class="upload-label">Выбрать фото</span>
                    <div id="fileName" class="file-name">Файлы не выбраны</div>
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

            <div class="form-group" id="colorOptions">
                <label>Выберите цвет фона</label>
                <select id="bgColor">
                    <option value="#ffffff">⬜ Белый</option>
                    <option value="#e0f2fe">🟦 Голубой</option>
                    <option value="#d1fae5">🟩 Зелёный</option>
                    <option value="#fef3c7">🟨 Жёлтый</option>
                    <option value="#1a1a2e">⬛ Тёмный</option>
                    <option value="#f472b6">💗 Розовый</option>
                    <option value="#fb923c">🟧 Оранжевый</option>
                    <option value="#a78bfa">🟪 Фиолетовый</option>
                    <option value="#ef4444">🔴 Красный</option>
                </select>
            </div>

            <div class="form-group hidden" id="imageOptions">
                <label>🖼️ Загрузите картинку для фона</label>
                <div class="upload-box" onclick="document.getElementById('bgFileInput').click()">
                    <input type="file" id="bgFileInput" accept="image/*">
                    <span class="upload-label">Выбрать фон</span>
                    <div id="bgFileName" class="file-name">Файл не выбран</div>
                </div>
            </div>

            <div class="form-group hidden" id="gradientOptions">
                <label>🌈 Цвета градиента</label>
                <input type="text" id="gradientColors" value="#6366f1, #8b5cf6">
                <div style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap;">
                    <button type="button" class="upload-label" onclick="setGradient('#6366f1,#8b5cf6')">Фиолетовый</button>
                    <button type="button" class="upload-label" onclick="setGradient('#f093fb,#f5576c')">Розовый</button>
                    <button type="button" class="upload-label" onclick="setGradient('#4facfe,#00f2fe')">Голубой</button>
                    <button type="button" class="upload-label" onclick="setGradient('#43e97b,#38f9d7')">Зелёный</button>
                    <button type="button" class="upload-label" onclick="setGradient('#fa709a,#fee140')">Закат</button>
                </div>
            </div>

            <!-- ЧЕКБОКС ТЕПЕРЬ ВСЕГДА ВИДЕН (вынесен из gradientOptions) -->
            <div class="checkbox-group">
                <input type="checkbox" id="upscale" name="upscale">
                <label for="upscale">🔍 Улучшить качество (увеличение 2x)</label>
            </div>

            <button class="btn-primary" onclick="sendImage()">🚀 Обработать</button>

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
                const files = e.target.files;
                if (files.length === 1) {
                    document.getElementById('fileName').textContent = files[0].name;
                } else {
                    document.getElementById('fileName').textContent = `${files.length} файлов`;
                }
                if (files.length > 0) {
                    originalImageUrl = URL.createObjectURL(files[0]);
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
                const files = fileInput.files;
                if (files.length === 0) {
                    alert('📸 Сначала выберите фото!');
                    return;
                }

                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `
                    <div class="spinner"></div>
                    <p class="status-text" id="progressText">⏳ Обработка 0 из ${files.length}...</p>
                `;

                const bgType = document.querySelector('input[name="bg_type"]:checked').value;
                const upscale = document.getElementById('upscale').checked;
                const bgColor = document.getElementById('bgColor').value;
                const bgFile = document.getElementById('bgFileInput').files[0];
                const gradColors = document.getElementById('gradientColors').value;

                // Собираем все результаты
                const results = [];
                let successCount = 0;

                for (let i = 0; i < files.length; i++) {
    document.getElementById('progressText').textContent = 
        `⏳ Обработка ${i + 1} из ${files.length}...`;

    // ЗАДЕРЖКА МЕЖДУ ЗАПРОСАМИ (1 секунда)
    if (i > 0) {
        await new Promise(r => setTimeout(r, 1200));
    }

    const formData = new FormData();
    // ... остальной код без изменений
                    formData.append('files', files[i]);
                    formData.append('bg_type', bgType);

                    if (bgType === 'color') {
                        formData.append('bg_color', bgColor);
                    } else if (bgType === 'image' && bgFile) {
                        formData.append('bg_image', bgFile);
                    } else if (bgType === 'gradient') {
                        formData.append('gradient_colors', gradColors);
                    }

                    if (upscale) {
                        formData.append('upscale', 'true');
                    }

                    try {
                        const response = await fetch('/process-multiple', {
                            method: 'POST',
                            body: formData
                        });

                        if (!response.ok) {
                            console.error(`Ошибка на фото ${i + 1}`);
                            continue;
                        }

                        const blob = await response.blob();
                        results.push({ blob, name: files[i].name });
                        successCount++;
                    } catch (error) {
                        console.error(`Ошибка на фото ${i + 1}:`, error);
                    }
                }

                if (results.length === 0) {
                    resultDiv.innerHTML = `<p class="error-text">❌ Не удалось обработать ни одного фото</p>`;
                    return;
                }

                // Если одно фото — показываем как PNG
                if (results.length === 1) {
                    const blob = results[0].blob;
                    currentResultBlob = blob;
                    const resultUrl = URL.createObjectURL(blob);

                    const originalHtml = originalImageUrl 
                        ? `<div class="compare-item">
                            <img src="${originalImageUrl}" alt="Исходное" />
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
                } else {
                    // Если несколько — собираем ZIP на клиенте
                    const zip = new JSZip();
                    for (const item of results) {
                        zip.file(`result_${item.name}`, item.blob);
                    }
                    const zipBlob = await zip.generateAsync({ type: 'blob' });
                    currentResultBlob = zipBlob;

                    resultDiv.innerHTML = `
                        <p style="color: #6ee7b7; text-align: center; padding: 20px; font-size: 15px;">
                            ✅ Готово! Обработано ${successCount} из ${files.length} фото
                        </p>
                        <div class="btn-group">
                            <button class="btn-download" onclick="downloadResult()">⬇️ Скачать ZIP</button>
                            <button class="btn-reset" onclick="resetApp()">🔄 Новое фото</button>
                        </div>
                    `;
                }
            }

            function downloadResult() {
                if (!currentResultBlob) {
                    alert('Нет результата!');
                    return;
                }
                const link = document.createElement('a');
                link.href = URL.createObjectURL(currentResultBlob);
                link.download = currentResultBlob.type === 'application/zip' ? 'results.zip' : 'result.png';
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
                document.getElementById('fileName').textContent = 'Файлы не выбраны';
                document.getElementById('bgFileInput').value = '';
                document.getElementById('bgFileName').textContent = 'Файл не выбран';
                document.getElementById('upscale').checked = false;
                currentResultBlob = null;
                originalImageUrl = null;
            }
        </script>
    </body>
    </html>
    """

@app.post("/process-multiple")
async def process_multiple(
    files: UploadFile = File(...),
    bg_type: str = Form("color"),
    bg_color: str = Form(None),
    bg_image: UploadFile = File(None),
    gradient_colors: str = Form(None),
    upscale: str = Form(None)
):
    # Теперь обрабатываем ТОЛЬКО ОДНО фото за запрос
    image_data = await files.read()
    foreground_bytes = remove_background(image_data)
    
    bg_image_bytes = None
    if bg_image and bg_image.filename:
        bg_image_bytes = await bg_image.read()
    
    result_image = add_background(foreground_bytes, bg_type, bg_color, bg_image_bytes, gradient_colors)
    
    if upscale == 'true':
        output = io.BytesIO()
        result_image.save(output, format="PNG")
        upscaled = upscale_image(output.getvalue(), scale=2)
        result_image = Image.open(io.BytesIO(upscaled))
    
    file_path = "temp/result.png"
    result_image.save(file_path, "PNG")
    return FileResponse(file_path, media_type="image/png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
