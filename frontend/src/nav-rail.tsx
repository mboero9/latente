import { useCallback, useEffect, useRef, useState } from "preact/hooks";
import type { ComponentChildren } from "preact";

type NavRailProps = { children: ComponentChildren; activePath: string };

/** Horizontally scrollable, keyboard-accessible navigation with explicit controls.
 * Overflow never removes sports: arrows, slider and touch scroll all work.
 */
export function NavRail({ children, activePath }: NavRailProps) {
  const navRef = useRef<HTMLElement>(null);
  const [position, setPosition] = useState({ left: 0, max: 0 });

  const measure = useCallback(() => {
    const node = navRef.current;
    if (!node) return;
    const max = Math.max(0, node.scrollWidth - node.clientWidth);
    setPosition({ left: Math.max(0, Math.min(max, node.scrollLeft)), max });
  }, []);

  useEffect(() => {
    const node = navRef.current;
    if (!node) return;
    const onScroll = () => measure();
    const resizeObserver = typeof ResizeObserver !== "undefined"
      ? new ResizeObserver(onScroll) : null;
    resizeObserver?.observe(node);
    // Observe menu content too, so translations/font loading do not hide entries.
    const links = node.firstElementChild;
    if (links) resizeObserver?.observe(links);
    node.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    document.fonts?.ready.then(onScroll).catch(() => {});
    onScroll();
    return () => {
      resizeObserver?.disconnect();
      node.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [measure]);

  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    // The selected sport is always brought back into the viewport after
    // navigation, without shifting the entire document.
    const active = nav.querySelector<HTMLElement>('a[aria-current="page"]');
    if (active) {
      const target = active.offsetLeft - nav.offsetLeft
        - (nav.clientWidth - active.offsetWidth) / 2;
      nav.scrollTo({ left: Math.max(0, target), behavior: "smooth" });
    }
  }, [activePath]);

  const shift = (direction: -1 | 1) => {
    const nav = navRef.current;
    if (!nav) return;
    nav.scrollBy({ left: direction * Math.max(150, nav.clientWidth * 0.68), behavior: "smooth" });
  };
  const overflow = position.max > 2;
  const percentage = position.max ? Math.round(position.left / position.max * 100) : 0;
  return <div class={"nav-rail" + (overflow ? " nav-rail-overflow" : "")}>
    <div class="nav-rail-row">
      <button type="button" class="nav-rail-arrow" aria-label="Ver actividades anteriores"
        title="Actividades anteriores" disabled={!overflow || position.left <= 2}
        onClick={() => shift(-1)}><span aria-hidden="true">‹</span></button>
      <nav class="top-nav" aria-label="Navegación principal" ref={navRef}>
        <span class="top-nav-items">{children}</span>
      </nav>
      <button type="button" class="nav-rail-arrow" aria-label="Ver más actividades"
        title="Más actividades" disabled={!overflow || position.left >= position.max - 2}
        onClick={() => shift(1)}><span aria-hidden="true">›</span></button>
    </div>
    {overflow && <div class="nav-rail-slider">
      <label class="sr-only" for="sports-nav-position">Deslizar actividades deportivas</label>
      <input id="sports-nav-position" type="range" min={0} max={100} step={1}
        value={percentage} aria-label="Deslizar actividades deportivas"
        onInput={event => {
          const nav = navRef.current;
          if (!nav) return;
          const pct = Number(event.currentTarget.value);
          nav.scrollLeft = (pct / 100) * Math.max(0, nav.scrollWidth - nav.clientWidth);
          measure();
        }} />
    </div>}
  </div>;
}
