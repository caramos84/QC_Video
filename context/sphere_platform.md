# SPHERE — plataforma de 6 engines (fuente: Figma "Validator_Focus")

Figma: https://www.figma.com/design/UoOqmXGtNjIGxJFl6FNTrh/Validator_Focus
Design tokens: [sphere_design_tokens.md](sphere_design_tokens.md)

**SPHERE** es un "Centro de Control de Calidad y Validación — Plataforma Interna", con un dashboard (sidebar: Dashboard / Proyectos / Revisar guías / Brand / Settings) y **6 engines de validación** especializados por tipo de asset:

| Engine | Enfoque | Descripción (mockup) |
|---|---|---|
| **Sherlock** | Visual Inspection Engine | Zonas seguras, puntos críticos, cumplimiento de marca, integridad compositiva — para **recursos estáticos** |
| **Pixduct** | HTML5 & Display Ad Validation | Código de banners HTML5, estructura ZIP, límites de peso, clickTag, dimensiones |
| **Highcut** | Video & Motion Graphics QA | Frame rates, códecs, formatos de exportación, duración — reproducción fluida cross-plataforma |
| **Experival** | UX/UI & Accessibility Audit | Cuadrículas, espaciado, contraste de color, accesibilidad, coherencia de componentes |
| **Ripcheck** | Print & Packaging Final Art | Archivos listos para imprimir, sangrados, plantillas de corte, perfiles de color |
| **Echoval** | Audio Engineering & Levels | *(texto del card en el mockup es un placeholder duplicado del de Sherlock — no tomar su alcance como definitivo)* |

## Decisión de alcance (confirmada 2026-08-06)

- **Este repo (`QC_Video`) es el backend de Highcut.** No es un proyecto aparte de SPHERE.
- **La capa sonora se queda dentro de Highcut** (no se separa hacia un futuro engine "Echoval" todavía).

## Por qué importa para el roadmap

La descripción de Highcut nombra explícitamente **códecs** y **frame rates** como parte de su función central — y hoy ambos son reglas `NOT_EVALUATED` (`TECH_CODEC`, y no existe check de frame rate) porque `metadata.json` (Notebook 01) no los captura. Es la señal más clara de qué cerrar primero en la capa técnica.

## Otros hallazgos

- Página "Componentes" del Figma: librería de UI completa y madura (Button, Input, Badge/Chip, Alert, Navbar, Checkbox/Radio/Toggle, Loader, Progress Bar, Avatar, Breadcrumbs, Tooltip, Calendario, Pop-up, List, Action Sheet, Context Menu, Dropdown, Cards, Tabs, Paginación, Stepper) — suficiente para construir el dashboard SPHERE real, no solo tokens.
- Los colores semánticos del design system (`Green_success`, `Yellow_warning`, `Red_danger`, `Blue_information`) mapean naturalmente al `Verdict` (PASS/REVIEW/FAIL) que ya produce el motor.
- Hay una exploración de logo suelta ("OCX") en la página de Componentes que no parece relacionada con SPHERE — posible inclusión accidental, sin confirmar.
