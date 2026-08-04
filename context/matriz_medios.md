# Matriz de medios — specs técnicos de video por plataforma

Investigado directamente en fuentes oficiales (Meta Business Help Center, TikTok For Business, Google Ads/DV360 Help, LinkedIn Marketing Solutions, Pinterest Business, IAB Tech Lab, Amazon Ads) en agosto 2026. Ver `matriz_medios.json` para la versión estructurada que alimentará el motor de reglas QC.

**Convención:** "no especificado" significa que la fuente oficial consultada NO publica ese dato (verificado por fetch directo), no que falte investigación.

## Meta (Facebook + Instagram)

| Placement | Aspect Ratio | Resolución (min/rec) | Duración (min–max) | Tamaño máx. | Códec/Contenedor | Bitrate | Captions | Safe zone | Audio |
|---|---|---|---|---|---|---|---|---|---|
| Facebook Feed | 4:5 rec. | 1440×1800 / mín 120×120 | 1s – 241min | 4 GB | MP4/MOV/GIF, H.264, progresivo | no esp. | Opcional | No especificado | AAC estéreo ≥128kbps, opcional |
| Instagram Feed | 9:16 rec. (±1%) | 1080×1920 / mín ancho 250px | 1s – 60min | 4 GB | MP4/MOV/GIF | no esp. | Opcional | No especificado | Opcional |
| Facebook Stories | 9:16 (±1%) | 1440×2560 / mín ancho 250px | 1s – 3min (>15s se divide en tarjetas) | 4 GB | MP4/MOV/GIF, H.264, progresivo | no esp. | Opcional | ~14% top / 20% bottom | AAC estéreo ≥128kbps |
| Instagram Stories | 9:16 (±1%) | 1440×2560 / mín ancho 250px | 1s – 60min | 4 GB | MP4/MOV/GIF, H.264, progresivo | no esp. | Opcional | ~14% top / 35% bottom / 6% lados | AAC estéreo ≥128kbps |
| Facebook Reels | 9:16 | 1440×2560 | sin máx. especificado | 4 GB | MP4/MOV/GIF, H.264, progresivo | no esp. | Opcional (auto-captions no soportado) | ~14% top / 35% bottom / 6% lados | AAC estéreo ≥128kbps |
| Instagram Reels | 9:16 | 1440×2560 / mín ancho 250px (<30s) o 500px (≥30s) | 0s – 15min | 4 GB | MP4/MOV, H.264, progresivo | no esp. | Opcional | ~14% top / 35% bottom / 6% lados | AAC estéreo ≥128kbps |
| Facebook In-Stream | 16:9 o 1:1 | mín 1080×1080 | Desktop 5–15s; Mobile 5s–10min | 4 GB | MP4/MOV/GIF, H.264, progresivo | no esp. | Opcional | No especificado | AAC estéreo >128kbps |

**Base común Meta:** H.264, contenedor MP4/MOV/GIF, AAC estéreo, tope 4GB — repetido en todas las páginas de placement (no es específico de un placement).

## TikTok

| Placement | Aspect Ratio | Resolución mín. | Duración | Tamaño máx. | Formato | Bitrate | Captions | Safe zone | Audio |
|---|---|---|---|---|---|---|---|---|---|
| In-Feed Ads (Auction/self-serve) | 9:16 vertical (rec.) / 16:9 / 1:1 | 540×960 (V) / 960×540 (H) / 640×640 (1:1) | hasta 10min | ≤500 MB | .mp4/.mov/.mpeg/.3gp/.avi | ≥516 kbps | Auto-generado, máx 4 líneas visibles | Zonas seguras descargables (no cuantificadas en px) | Obligatorio (todo creativo debe sonar) |
| In-Feed Reach & Frequency (reservation) | igual | 5 – 60s (rec. 9–15s) | ≤500 MB | igual | ≥2500 kbps | igual | igual | Obligatorio |
| TopView / Brand Takeover | 9:16 | 540×960 | 5 – 60s (rec. 9–15s) | ≤500 MB | .mp4/.mov/.mpeg/.3gp | ≥2500 kbps | Máx 100 car. / 4 líneas (50 car. CN/JP/KR) | "initial-stage" (3s, zoom-in) vs "feed-stage" — evitar blanco puro en 1º 3s | Obligatorio, evitar sonidos abruptos en 1º 3s |

**Nota:** "In-Feed" en TikTok NO es un solo spec — difiere entre compra self-serve (Auction) y reservada (Reach & Frequency). Spark Ads (boost de post orgánico) no tiene restricción de duración.

## Google / YouTube / DV360 (Programmatic)

| Formato | Aspect Ratio | Resolución (min/rec) | Duración | Tamaño máx. | Contenedor | Frame rate | Bitrate | Audio |
|---|---|---|---|---|---|---|---|---|
| GDN Responsive Display (video vía YouTube link) | 16:9, 1:1, 2:3 | hereda de YouTube | libre, rec. 30s | n/a (es link) | n/a | no esp. | no esp. | no esp. |
| GDN/DV360 In-banner video (HTML5) | 4:3 rec. | video máx 4096×4096 | reproducción ≤4min; apertura ≤30s | 40KB carga inicial / 2.2MB total | no esp. | mín 14fps, 30fps rec. | no esp. | ≤ -12dB |
| YouTube In-stream skippable | 16:9, 9:16, 1:1 | rec. 1080p / mín 720p | libre (reserva: 12s–6min) | ≤256 GB | MP4/MPEG rec.; también WMV/AVI/MOV/FLV/WebM/HEVC | no esp. | no esp. | embebido, no solo-audio |
| YouTube In-stream non-skippable | 16:9/4:3 (H), 9:16/2:3 (V), 1:1 | rec. 1080p / mín 720p o 640×480 | 7–15s | ≤256 GB | igual | no esp. | no esp. | igual |
| YouTube Non-skippable 30s (CTV) | solo 16:9 horizontal | rec. 1080p / mín 720p | 16–30s | ≤256 GB | igual | no esp. | no esp. | igual |
| YouTube Bumper | 16:9, 9:16, 1:1 | rec. 1080p / mín 720p/480p | ≤6s fijo | ≤256 GB | igual | no esp. | no esp. | igual |
| YouTube Shorts ads | 9:16 (primario), H/cuadrado también | 720×1280 (V) / 480×480 / 1280×720 (H) | mín 5–10s; máx técnico 3min (feed reproduce 60s) | ≤256GB (asumido) | familia MP4 | no esp. | no esp. | no esp. |
| YouTube Video action / Demand Gen | 1:1, 16:9, 4:5, 9:16 | 1080×1080 / 1920×1080 / 1080×1350 / 1080×1920 | mín 5s (10s p/elegibilidad in-stream); rec. >15s | ≤256GB | MPG (MPEG-2/4) | no esp. | no esp. | puede correr sin sonido |
| DV360/Programmatic VAST (IAB DV&CTV Guidelines v2.0) | 16:9 rec.; 21:9 opcional; 1:1/9:16 nonlinear | escalera 640×360 → 3840×2160 (4K CTV) | comunes 6/15/20/30s; short 3–10s; hasta 60s | 1GB fuente subido DV360; ≤10MB servido | H.264 High Profile MP4 requerido; opcional H.265/VP9/AV1 (CTV) | 23.976/24/25/29.97/30/50/59.94/60 | 360p 1.5–3Mbps · 480/540p 2–4Mbps · 720p 2–5Mbps · 1080p 4–10Mbps · 4K 15–30Mbps | AAC-LC (Dolby 5.1 opcional CTV); 128–192kbps estéreo / 256–384kbps surround; 48kHz pref.; loudness -24LKFS±2 (US) / -23LUFS±1 (EU); pico ≤-6dBTP |

VAST soportado en DV360: 2.0, 3.0, 4.x (vigente 4.x).

## LinkedIn

| Formato | Aspect Ratio | Resolución | Duración | Tamaño máx. | Formato | Frame rate | Audio |
|---|---|---|---|---|---|---|---|
| Video Ads (Sponsored Content) | 4:5, 9:16, 16:9, 1:1 (±5%) | 360–1920px por lado (ej. 1080×1350, 1080×1920, 1920×1080) | 3s – 30min | 75KB – 500MB | MP4 | 30fps rec. | AAC o MPEG4, sample rate <64kHz |
| Thought Leader Ads (video) | no esp. por separado — usa specs de video nativo/post orgánico | no esp. | 3s – 15min (spec de post nativo) | hasta 5GB (nativo, no de ad estándar) | MP4 | no esp. | no esp. |

## Pinterest

| Formato | Aspect Ratio | Resolución | Duración | Tamaño máx. | Formato | Bitrate/FPS/Captions/Audio |
|---|---|---|---|---|---|---|
| Standard Width Video Ads | entre 1:2 y 1.91:1; rec. 1:1, 2:3, 4:5, 9:16 | no especificado en px | 4s – 15min (rec. 6–15s) | ≤2GB | .MP4/.MOV/.M4V, H.264/H.265 | no especificado (ninguno de estos 4 campos está publicado por Pinterest) |
| Max Width Video Ads | no excede altura 1:1 (~1:1 a 16:9) | no especificado | 4s – 15min (rec. 6–15s) | ≤2GB | .MP4/.MOV/.M4V, H.264/H.265 | no especificado |

## CTV / OTT

| Fuente | Aspect Ratio | Resolución | Duración | Tamaño máx. | Codec/Contenedor | Frame rate | Bitrate | Audio |
|---|---|---|---|---|---|---|---|---|
| IAB DV & CTV Ad Format Guidelines (estándar de industria — "común denominador") | 16:9 pref. (4:3 si fuente lo es; 21:9 emergente) | 1280×720 o 1920×1080 | 6/15/30s estándar; 3–10s bumper; hasta 60s | no esp. (varía por publisher) | H.264 MP4 (progressive); HLS/MPEG-DASH (adaptive) | mantener original: 23.976/25/29.97 | ~15,000–30,000 kbps target CTV | AAC-LC/HE-AACv1 128–192kbps; 2.0 (5.1 opcional); 44.1/48kHz; loudness -24LKFS±2 (US/ATSC) o -23LUFS±1 (EU/EBU); pico ≤-6dBTP |
| Amazon Ads Streaming TV / Prime Video (ejemplo de plataforma real) | 16:9 | mín 1920×1080 | 15/30/45/60s (Prime Video US); 3P apps: 6/10/15/20/30/45/60/75/90s | 500MB | H.264/MPEG-2/MPEG-4, MP4/M2T/TS | 23.976 rec./24/25/29.97 constante | mín 15Mbps (Prime Video) / 8Mbps (Twitch/Fire TV/3P); rec. 50Mbps | AAC, mín 192kbps, 44.1/48kHz, mín 2 canales |

Nota: no existe una única "plataforma CTV" — se usó IAB como estándar de referencia y Amazon como ejemplo real representativo. Hay una revisión IAB en comment público (dic-2025/ene-2026) que añade 6 formatos nuevos (pause, menu, overlay, in-scene, screensaver, squeezeback), aún no reemplaza las specs base citadas.

## Campos con incertidumbre real (no solo falta de investigación)

- **Frame rate en Meta**: nunca se publica un valor numérico (dicen "fixed frame rate, progressive scan"). No usar 30fps como regla dura de Meta.
- **Bitrate/captions en la mayoría de placements de Meta, TikTok In-Feed (fps), YouTube (bitrate), Pinterest (casi todo)**: no publicado — para reglas duras de validación técnica, estos campos deben quedar como "no aplica / no verificable" en vez de inventarse un umbral.
- Donde no hay dato duro de plataforma pero se necesita un umbral técnico para programática/CTV, usar los rangos de IAB como referencia (son prescriptivos).

## Fuentes completas

Meta: facebook.com/business/ads-guide/update/video (+ subpáginas por placement) · TikTok: ads.tiktok.com/help (auction in-feed, reservation in-feed R&F, TopView) · Google/YouTube: support.google.com/google-ads (video specs, skippable/non-skippable/bumper/shorts/demand-gen), support.google.com/displayvideo (in-banner, video creatives, ad formats) · IAB Tech Lab: Ad-Format-Guidelines_DV-CTV.pdf (+ revisión dic-2025 en GitHub) · LinkedIn: business.linkedin.com/advertise/ads/sponsored-content (video-ads, thought-leader-ads specs) · Pinterest: help.pinterest.com (pinterest-product-specs, promoted-video-with-autoplay) · Amazon Ads: advertising.amazon.com/resources/ad-specs/dsp/video/streaming-tv-prime-video-ads
