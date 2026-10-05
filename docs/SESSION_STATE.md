# Session State — 2026-10-05

## Aktuálny stav
- Posledný commit: be2a298 (observability)
- Všetko pushnuté, main == origin/main
- Render backend + frontend auto-deploy

## Hotové vrstvy kvality
1. Zálohy DB — d720f58 + cron (0 3 * * *)
2. CI/CD — BLOKOVANÉ GitHub Support ticketom
3. Bezpečnosť — signed URLs (9096160, 51c9520)
4. Kvalita leadov — D2 filter (38bb0ba)
5. Observability — be2a298 (/ready, summary, metrics, scheduler alerts)

## Bonus features
- ZS category discovery (296 firiem): 7612826
- Auto-approve + batch send: 23910be
- Telegram bot + webhook: aec1a1b, 391b98d
- Edit listing + thumbnails: c31f6f8
- DB fields phone/website/source_url: e236a60

## Aktuálne problémy (2026-10-05)
- Admin UI nevidí tlačidlá "Auto-schváliť s emailom" + "Auto-send batch (30)"
- Moje ponuky nezobrazuje thumbnail vpravo
- Podozrenie: frontend build na Renderi je starý

## Deployment info
- Backend: srv-dak1fp942lol73bl6ubg (waste-platform, Python)
- Frontend: srv-dal7p0rm8rtd73f72340 (waste-platform-web, Node)
- DB: dpg-dakh3fe1egvs73bs262g-a
- Doména: trc-cmep.sk
- Cron backup: waste-platform-backup (0 3 * * *)

## Blokátory
- GitHub Actions: account-level startup_failure (Support ticket)
- Render billing: OK (zaplatené)
