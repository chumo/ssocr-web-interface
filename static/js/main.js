let cropper;
let lastCropData = null;
const imageContainer = document.getElementById('imageContainer');
const mainImage = document.getElementById('mainImage');
const resultText = document.getElementById('resultText');
const processedImage = document.getElementById('processedImage');

const commandUsed = document.getElementById('commandUsed');
const thresholdVal = document.getElementById('thresholdVal');

let currentImagePath = null;

document.getElementById('loadImageBtn').addEventListener('click', loadFromUrl);
document.getElementById('threshold').addEventListener('input', (e) => {
    const val = e.target.value;
    thresholdVal.textContent = val == -1 ? 'Auto' : val + '%';
    if(shouldAutoProcess()) processImage();
});
document.getElementById('digits').addEventListener('change', () => { if(shouldAutoProcess()) processImage(); });
document.getElementById('invertColors').addEventListener('change', () => { if(shouldAutoProcess()) processImage(); });
document.getElementById('extraOptions').addEventListener('change', () => { if(shouldAutoProcess()) processImage(); });
document.getElementById('extraArgs').addEventListener('change', () => { if(shouldAutoProcess()) processImage(); });
document.getElementById('processBtn').addEventListener('click', processImage);

function shouldAutoProcess() {
    return document.getElementById('autoProcess').checked && cropper;
}



async function loadFromUrl() {
    const url = document.getElementById('imageUrl').value;
    if (!url) return;

    try {
        const response = await fetch(`/proxy-image?url=${encodeURIComponent(url)}`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Save last crop data if exists
        if (cropper) {
            lastCropData = cropper.getData();
            cropper.destroy();
        }

        currentImagePath = data.path;
        mainImage.src = data.url + '?t=' + new Date().getTime();
        mainImage.style.display = 'block';

        cropper = new Cropper(mainImage, {
            viewMode: 2,
            autoCropArea: 0.8,
            zoomOnWheel: false,
            cropend: () => {
                if(shouldAutoProcess()) processImage();
            },
            ready: function() {
                // Restore previous crop data if available
                if (lastCropData) {
                    this.cropper.setData(lastCropData);
                }

                if(shouldAutoProcess()) processImage();
            }
        });

    } catch (e) {
        alert('Error loading image: ' + e.message);
    }
}

async function processImage() {
    if (!cropper || !currentImagePath) return;

    const cropData = cropper.getData();

    const payload = {
        image_path: currentImagePath,
        crop: {
            x: Math.max(0, cropData.x),
            y: Math.max(0, cropData.y),
            width: cropData.width,
            height: cropData.height
        },
        threshold: parseInt(document.getElementById('threshold').value),
        digits: parseInt(document.getElementById('digits').value),
        invert: document.getElementById('invertColors').checked,
        extra_options: document.getElementById('extraOptions').value,
        extra_args: document.getElementById('extraArgs').value
    };

    // UI Loading state
    const resultsPanelBody = document.getElementById('resultsPanelBody');
    resultText.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    // Reset styles
    resultsPanelBody.classList.remove('error-state');
    resultText.classList.remove('error-text');

    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
             // Handle HTTP error as application error
             throw new Error(data.details || data.error || 'Unknown error');
        }

        if (data.error) {
             // ssocr error
             resultsPanelBody.classList.add('error-state');
             resultText.classList.add('error-text');
             resultText.innerText = data.error + "\n" + (data.details || "");
        } else {
             // Success
             resultText.innerText = data.text;
        }

        if (data.debug_image) {
            // Append timestamp to prevent caching
            processedImage.src = data.debug_image + '?t=' + new Date().getTime();
            processedImage.style.display = 'block';
        }
        commandUsed.innerText = '$ ' + data.command;

    } catch (e) {
        console.error(e);
        resultsPanelBody.classList.add('error-state');
        resultText.classList.add('error-text');
        resultText.innerText = e.message;
        processedImage.style.display = 'none';
    }
}
