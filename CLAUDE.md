# Project Overview
Local Flask-based web application and static tool designed for warehouse operations. It reads hard drive catalog data from `hdd.json` to calculate carton shipping weights, layer configurations, and overall pallet dimensions (L × W × H). The app must run smoothly both when served over a local network (LAN) and as self-contained static HTML pages (`dist/`) that function completely offline without servers or internet connections.

# UI/UX & Industrial Design Philosophy
* **Aesthetic:** Modern, utilitarian, and clean with a distinct "industrial tool" vibe. The interface should evoke the reliability and precision of professional warehouse logistics software.
* **Information Hierarchy:** High signal-to-noise ratio. Deliver immediate operational answers (dimensions, total case counts, carton weights) without dense blocks of text.
* **Iconography & Visuals:** Prioritize recognized iconography, product thumbnails, badges, and company marks over explanatory paragraphs to prevent cognitive overload during fast-paced fulfillment workflows.
* **Cross-Platform Support:** Ensure responsive viewports across macOS, Windows, and mobile devices:
  * Windows/Mac scrollbar compensation: Maintain the scrollbar mask width (`--sbw`) dynamically to prevent horizontal layout shift.
  * Mobile adaptation: Collapse navigation rails into top banners under 940px and wrap product input grids under 620px.

# Motion & Interaction Standards (Senior Frontend Tier)
All interactive elements must provide tangible tactile feedback conforming to Emil Kowalski's motion principles:
* **Expanding Icon Bubbles:** Idle control buttons should display minimal icons and expand smoothly into labeled pill controls upon hover or focus to state their function clearly before contracting on release.
* **Tactile Option Scaling:** Interactive rows and options must provide subtle scale feedback (e.g., `scale(1.02)`) on hover, dipping on active press (`scale(0.97)` to `scale(0.98)`), followed by quick pop animations to confirm selection.
* **Performance-First Animation:** Animate GPU-accelerated properties (`transform`, `opacity`, and `clip-path`) rather than layout dimensions. Keep UI motion snappy (under 300ms) with strong ease-out curves (`cubic-bezier(0.23, 1, 0.32, 1)`).
* **Accessibility:** Strictly respect `prefers-reduced-motion: reduce` by replacing spatial travel with gentle opacity crossfades.

# Development & Architecture Directives
* **Data Single Source of Truth:** All drive specifications reside exclusively in `hdd.json`. Never hardcode capacity or weight logic in templates or Python handlers.
* **Zero Runtime Dependencies:** Frontend calculations, 3D projections, and interactive behaviors must run in vanilla JavaScript and CSS without external CDNs or third-party client libraries.