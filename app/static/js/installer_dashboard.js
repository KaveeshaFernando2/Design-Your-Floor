// Image preview before upload
document.addEventListener("DOMContentLoaded", () => {
    const photoInput = document.getElementById("photo");
    const previewContainer = document.getElementById("preview-container");

    if (photoInput) {
        photoInput.addEventListener("change", (event) => {
            previewContainer.innerHTML = ""; // clear previous preview
            const file = event.target.files[0];
            if (file) {
                const img = document.createElement("img");
                img.src = URL.createObjectURL(file);
                img.style.maxWidth = "200px";
                img.style.marginTop = "10px";
                img.style.borderRadius = "10px";
                previewContainer.appendChild(img);
            }
        });
    }
});
