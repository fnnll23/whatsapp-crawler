const infoBtn = document.querySelector('.js-infoIcon');
const infoModal = document.querySelector('.js-infoModal');
infoBtn.onclick = showInfo;

function showInfo() {
    infoModal.classList.toggle("visible-flex");
}
