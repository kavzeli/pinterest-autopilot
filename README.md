# Pinterest autopilot for WellKind Daily

Every day a Claude Code routine reads the newest articles on wellkinddaily.com,
makes 5 pins (Flux background from Cloudflare + your headline and branding),
pushes the images here so they have public links, and adds them to your Buffer
queue. Buffer publishes them to Pinterest at your queue times.

The routine follows `ROUTINE.md`. Change that file to change what it does.

## Files

| File | What it does |
| --- | --- |
| `ROUTINE.md` | The instructions Claude follows on every run |
| `config.json` | Your site, brand, Pinterest board name, GitHub repo, pins per day, colours |
| `scripts/get_articles.py` | Lists new articles that still need pins |
| `scripts/make_pins.py` | Generates the Flux background and lays out each 1000 x 1500 pin |
| `scripts/post_pins.py` | Adds the pins to the Buffer queue and logs them |
| `scripts/check_setup.py` | Tests that the website, Cloudflare and Buffer are all connected |
| `data/posted.json` | Log of every pin queued, so articles are not pinned twice |
| `pins/` | The pin images, one folder per day |
| `fonts/` | Lora and Inter (SIL Open Font License, see `fonts/OFL.txt`) |

## Settings the routine needs

Environment variable (in the cloud environment):

- `CLOUDFLARE_ACCOUNT_ID` = your Cloudflare account ID

Network secrets (the keys are added to requests automatically, never visible):

- Host `api.cloudflare.com`, header `Authorization`, prefix `Bearer`, value = Cloudflare API token
- Host `api.buffer.com`, header `Authorization`, prefix `Bearer`, value = Buffer API key

Allowed domains (network access set to Custom, with the default list ticked):

- `wellkinddaily.com`

## Troubleshooting

| What you see | What to do |
| --- | --- |
| `FAIL Cloudflare ... 401` or `403` | Re-create the Cloudflare secret: host `api.cloudflare.com`, prefix `Bearer`, and a token made from the **Workers AI** template |
| `CLOUDFLARE_ACCOUNT_ID ... missing` | Add `CLOUDFLARE_ACCOUNT_ID=...` under Environment variables |
| Pins have a plain green/cream background | Flux failed; the run report has the error. Usually the Cloudflare token or daily free limit |
| `Buffer refused the request` | Re-create the Buffer secret for host `api.buffer.com` with a fresh key from publish.buffer.com/settings/api |
| `No Pinterest channel is connected` | In Buffer, connect your Pinterest account as a channel |
| `No Pinterest board named ...` | Set `pinterest_board_name` in `config.json` to the exact board name listed in the error |
| `Could not list Pinterest boards automatically` | Put the board ID in `pinterest_board_service_id` in `config.json` |
| `image is not public yet` | Check the repository is **Public** and `github_repo` in `config.json` is right |
| `Could not read articles (403)` | Add `wellkinddaily.com` to the environment's Allowed domains |
| Push to `main` rejected | Make sure `main` has no branch protection rules; the routine falls back to `claude/pins` |
| Buffer queue is full | The free plan holds 10 queued posts per channel. Lower `pins_per_day` or add more daily times in Buffer |
