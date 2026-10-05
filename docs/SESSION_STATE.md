# Session State — 2026-10-05

## Aktuálny stav
- Posledný commit: 92ab304 (PLATFORM_MAP)
- main == origin/main
- Render backend + frontend auto-deploy, ak web UI zaostáva, redeploy waste-platform-web

## Zatvorené od starého snapshotu
- Auto-schváliť / auto-send-batch sú v page.tsx (b05a91c)
- Thumbnail na mobile nie je schovaný pod sm (6bd21ed)
- SignedImage je v listings page (51c9520)
- commands=false, break_glass=false

## Ešte nie v tomto commite
- GitHub Actions startup_failure — účet, nie kód
- UPLOADS_REQUIRE_SIGNED ostáva false, kým formuláre nepoužívajú SignedImage
- Joomla cloak gmail len ak CLOAK_FILTERED v tomto behu

## Deployment
- Backend: srv-dak1fp942lol73bl6ubg
- Frontend: srv-dal7p0rm8rtd73f72340
- Doména: trc-cmep.sk
