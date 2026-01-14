(function () {
  const root = document.documentElement;

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

// Set CSS var for topbar height (used by full-width submenu positioning)
const topbar = document.querySelector('.topbar');
function setTopbarHeightVar(){
  if(!topbar) return;
  const h = Math.ceil(topbar.getBoundingClientRect().height);
  document.documentElement.style.setProperty('--topbar-h', h + 'px');
}
setTopbarHeightVar();
window.addEventListener('resize', setTopbarHeightVar);

  // Theme
  const themeToggle = document.getElementById("themeToggle");
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
    });
  }

  // Drawer (tablet/mobile) + accordion
  const menuToggle = document.getElementById("menuToggle");
  const menuClose = document.getElementById("menuClose");
  const drawer = document.getElementById("drawer");
  const drawerNav = document.getElementById("drawerNav");
  const navTree = window.__NAV_TREE__ || [];

  function openDrawer() {
    if (!drawer) return;
    drawer.removeAttribute("hidden");
    if (menuToggle) menuToggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.setAttribute("hidden", "");
    if (menuToggle) menuToggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  if (menuToggle && drawer) {
    menuToggle.addEventListener("click", () => {
      const isHidden = drawer.hasAttribute("hidden");
      if (isHidden) openDrawer();
      else closeDrawer();
    });
  }
  if (menuClose) menuClose.addEventListener("click", closeDrawer);

  if (drawer) {
    drawer.addEventListener("click", (e) => {
      if (e.target === drawer) closeDrawer();
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !drawer.hasAttribute("hidden")) closeDrawer();
    });
  }

  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 981px)").matches) closeDrawer();
  });

  if (drawerNav) {
    drawerNav.innerHTML = navTree.map((n) => renderNode(n, 0)).join("");
    drawerNav.querySelectorAll("[data-acc-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-acc-toggle");
        const acc = drawerNav.querySelector(`[data-acc='${cssEscape(id)}']`);
        if (!acc) return;
        const expanded = acc.getAttribute("aria-expanded") === "true";
        acc.setAttribute("aria-expanded", expanded ? "false" : "true");
      });
    });
  }

  function renderNode(node, depth) {
    const hasKids = node.children && node.children.length;
    const indentClass = depth > 0 ? " acc__child--indent" : "";
    if (!hasKids) {
      return `<a class="drawer__leaf${indentClass}" href="${escAttr(node.url)}">${escHtml(node.title)}</a>`;
    }
    const id = "acc_" + hash(node.url);
    const kids = node.children.map((c) => renderChild(c, depth + 1)).join("");
    return `
      <section class="acc" data-acc="${escAttr(id)}" aria-expanded="false">
        <button class="acc__top" type="button" data-acc-toggle="${escAttr(id)}">
          <span>${escHtml(node.title)}</span>
          <span class="acc__chev">▾</span>
        </button>
        <div class="acc__panel">
          <a class="acc__child" href="${escAttr(node.url)}">${escHtml(node.title)} overview</a>
          ${kids}
        </div>
      </section>
    `;
  }

  function renderChild(node, depth) {
    const hasKids = node.children && node.children.length;
    const indentClass = depth > 0 ? " acc__child--indent" : "";
    if (!hasKids) {
      return `<a class="acc__child${indentClass}" href="${escAttr(node.url)}">${escHtml(node.title)}</a>`;
    }
    const id = "acc_" + hash(node.url);
    const kids = node.children.map((c) => renderChild(c, depth + 1)).join("");
    return `
      <div class="acc" data-acc="${escAttr(id)}" aria-expanded="false">
        <button class="acc__top" type="button" data-acc-toggle="${escAttr(id)}">
          <span>${escHtml(node.title)}</span>
          <span class="acc__chev">▾</span>
        </button>
        <div class="acc__panel">
          <a class="acc__child${indentClass}" href="${escAttr(node.url)}">${escHtml(node.title)} overview</a>
          ${kids}
        </div>
      </div>
    `;
  }

  // TOC
  const toc = document.getElementById("toc");
  const content = document.getElementById("content");
  if (toc && content) {
    const headings = content.querySelectorAll("h2, h3");
    const items = [];
    headings.forEach((h) => {
      if (!h.id) {
        h.id = h.textContent
          .toLowerCase()
          .trim()
          .replace(/[^\w\s-]/g, "")
          .replace(/\s+/g, "-");
      }
      const depth = h.tagName === "H3" ? 3 : 2;
      items.push({ id: h.id, text: h.textContent, depth });
    });

    toc.innerHTML = items.length
      ? items.map(it => `<a href="#${it.id}" data-depth="${it.depth}">${escapeHtml(it.text)}</a>`).join("")
      : `<div class="muted">No headings found.</div>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
  function escHtml(s){ return escapeHtml(s); }
  function escAttr(s){ return escapeHtml(s); }

  function hash(s){
    let h = 0;
    for (let i=0;i<s.length;i++){ h = ((h<<5)-h) + s.charCodeAt(i); h |= 0; }
    return String(Math.abs(h));
  }
  function cssEscape(s){
    return String(s).replace(/'/g,"\\'");
  }
// Desktop full-width submenu behavior (JS-controlled)
// Reason: fixed full-width bars are outside the normal hover chain; CSS :hover can flicker.
const mqDesktop = window.matchMedia("(min-width: 981px)");
const menuItems = Array.from(document.querySelectorAll(".menu__item.has-sub"));
let active = null;
let closeTimer = null;

function clearCloseTimer() {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function closeActive(immediate = false) {
  clearCloseTimer();
  const doClose = () => {
    if (active) {
      active.classList.remove("is-open");
      active = null;
    }
  };
  if (immediate) doClose();
  else closeTimer = setTimeout(doClose, 120);
}

function openItem(li) {
  clearCloseTimer();
  if (active && active !== li) active.classList.remove("is-open");
  active = li;
  li.classList.add("is-open");
}

function setupDesktopMenus() {
  // Clean any lingering state
  menuItems.forEach(li => li.classList.remove("is-open"));
  active = null;

  menuItems.forEach((li) => {
    const submenu = li.querySelector(":scope > .submenu");
    if (!submenu) return;

    // Open when entering the menu item (including link/chevron)
    li.addEventListener("pointerenter", () => {
      if (!mqDesktop.matches) return;
      openItem(li);
    });

    // Start close when leaving the menu item (but allow moving into submenu)
    li.addEventListener("pointerleave", (e) => {
      if (!mqDesktop.matches) return;
      // If we're moving into the submenu, don't close.
      if (submenu.contains(e.relatedTarget)) return;
      closeActive(false);
    });

    // Keep open while hovering submenu
    submenu.addEventListener("pointerenter", () => {
      if (!mqDesktop.matches) return;
      clearCloseTimer();
      openItem(li);
    });

    submenu.addEventListener("pointerleave", (e) => {
      if (!mqDesktop.matches) return;
      // If moving back to the parent item, don't close.
      if (li.contains(e.relatedTarget)) return;
      closeActive(false);
    });
  });

  // Clicking anywhere else closes
  document.addEventListener("pointerdown", (e) => {
    if (!mqDesktop.matches) return;
    const inMenu = e.target.closest(".menubar");
    if (!inMenu) closeActive(true);
  });

  // Esc closes
  window.addEventListener("keydown", (e) => {
    if (!mqDesktop.matches) return;
    if (e.key === "Escape") closeActive(true);
  });
}

setupDesktopMenus();

// When switching breakpoints, close immediately to avoid stuck state
mqDesktop.addEventListener("change", () => {
  closeActive(true);
});
})();
