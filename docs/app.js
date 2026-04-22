(function () {
  const tabs = Array.from(document.querySelectorAll(".gallery-tab"));
  const panels = Array.from(document.querySelectorAll(".gallery-panel"));

  function showPanel(targetId) {
    tabs.forEach((tab) => {
      const isActive = tab.dataset.target === targetId;
      tab.classList.toggle("is-active", isActive);
      tab.setAttribute("aria-selected", String(isActive));
    });

    panels.forEach((panel) => {
      const isActive = panel.id === targetId;
      panel.classList.toggle("is-active", isActive);
      panel.hidden = !isActive;
    });
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      showPanel(tab.dataset.target);
    });
  });

  const copyButton = document.querySelector("[data-copy-target]");
  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      const target = document.getElementById(copyButton.dataset.copyTarget);
      if (!target) {
        return;
      }

      try {
        await navigator.clipboard.writeText(target.textContent.trim());
        copyButton.classList.add("is-copied");
        copyButton.querySelector("span").textContent = "Copied";
        window.setTimeout(() => {
          copyButton.classList.remove("is-copied");
          copyButton.querySelector("span").textContent = "Copy BibTeX";
        }, 1400);
      } catch (error) {
        copyButton.querySelector("span").textContent = "Copy failed";
      }
    });
  }
})();
