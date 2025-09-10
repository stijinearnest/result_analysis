document.addEventListener("DOMContentLoaded", () => {
    const photoUpload = document.getElementById("photoUpload");
    const photoInput = document.getElementById("photo");
    const photoPreview = document.getElementById("photoPreview");
  
    if (photoUpload && photoInput && photoPreview) {
      photoUpload.addEventListener("click", () => photoInput.click());
  
      photoInput.addEventListener("change", () => {
        const file = photoInput.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = e => {
            photoPreview.src = e.target.result;
            photoPreview.style.display = "block";
            photoUpload.querySelector("p").style.display = "none";
            photoUpload.querySelector(".small").style.display = "none";
            photoUpload.querySelector(".upload-icon").style.display = "none";
          };
          reader.readAsDataURL(file);
        }
      });
    }
  });
  