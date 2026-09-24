document.querySelectorAll(".flash-close").forEach((button) => {
  button.addEventListener("click", () => button.parentElement.remove());
});

window.setTimeout(() => {
  document.querySelectorAll(".flash").forEach((flash) => {
    flash.classList.add("flash-leaving");
    window.setTimeout(() => flash.remove(), 250);
  });
}, 4500);