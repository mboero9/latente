import { useEffect, useRef } from "preact/hooks";

/**
 * Three intentionally quiet ad spaces.
 *
 * No ad vendor is contacted until the site has an approved publisher account,
 * individual placement IDs, and an explicitly enabled privacy setup.
 * See docs/MONETIZACION-PUBLICIDAD.md before enabling production requests.
 */
export type AdPlacementName = "top" | "side" | "bottom";

const publisherId = (import.meta.env.VITE_ADSENSE_CLIENT || "").trim();
const placementIds: Record<AdPlacementName, string> = {
  top: (import.meta.env.VITE_ADSENSE_SLOT_TOP || "").trim(),
  side: (import.meta.env.VITE_ADSENSE_SLOT_SIDE || "").trim(),
  bottom: (import.meta.env.VITE_ADSENSE_SLOT_BOTTOM || "").trim(),
};
const preview = import.meta.env.DEV || import.meta.env.VITE_AD_SLOTS_PREVIEW === "true";
const enabled =
  import.meta.env.VITE_ADSENSE_ENABLED === "true" &&
  import.meta.env.VITE_ADS_PRIVACY_READY === "true" &&
  /^ca-pub-\d+$/.test(publisherId);

let adsScript: Promise<void> | null = null;

function loadAdsense() {
  if (!adsScript) {
    adsScript = new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      script.async = true;
      script.crossOrigin = "anonymous";
      script.src =
        "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" +
        encodeURIComponent(publisherId);
      script.addEventListener("load", () => resolve(), { once: true });
      script.addEventListener("error", () => reject(new Error("AdSense script unavailable")), {
        once: true,
      });
      document.head.appendChild(script);
    }).catch((error) => {
      adsScript = null;
      throw error;
    });
  }
  return adsScript;
}

declare global {
  interface Window {
    adsbygoogle?: Record<string, unknown>[];
  }
}

export function AdPlacement({ placement }: { placement: AdPlacementName }) {
  const unit = useRef<HTMLModElement>(null);
  const alreadyRequested = useRef(false);
  const slotId = placementIds[placement];
  const serveAds = enabled && /^\d+$/.test(slotId);
  const showPreview = preview && !serveAds;

  useEffect(() => {
    if (!serveAds || !unit.current) return;

    let cancelled = false;
    const node = unit.current;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting) || alreadyRequested.current) {
          return;
        }
        observer.disconnect();
        // Skip hidden (responsive) or zero-width inventory.
        if (!node.getBoundingClientRect().width) return;
        alreadyRequested.current = true;
        void loadAdsense()
          .then(() => {
            if (!cancelled && node.isConnected) {
              (window.adsbygoogle = window.adsbygoogle || []).push({});
            }
          })
          .catch(() => {
            // Do not hide the editorial content when an ad network is unavailable.
          });
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => {
      cancelled = true;
      observer.disconnect();
    };
  }, [serveAds, slotId]);

  if (!serveAds && !showPreview) return null;
  return (
    <aside class={`latente-ad latente-ad--${placement}`} aria-label="Anuncios">
      <span class="latente-ad__label">Anuncios</span>
      {serveAds ? (
        <ins
          ref={unit}
          class="adsbygoogle latente-ad__unit"
          style={{ display: "block" }}
          data-ad-client={publisherId}
          data-ad-slot={slotId}
          data-ad-format={placement === "side" ? "rectangle" : "horizontal"}
          data-full-width-responsive="true"
        />
      ) : (
        <div class="latente-ad__preview" aria-label="Previsualización, no es un anuncio real">
          Espacio publicitario · vista previa
        </div>
      )}
    </aside>
  );
}
