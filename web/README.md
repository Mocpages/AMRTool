# Host the AMR website

The site in this folder is static. Roster CSV files, KMZ files, cached LZ pictures, and the filled PDF stay on the user’s computer (browser storage and their downloads folder). The host only serves HTML, JavaScript, CSS, and the blank template PDF.

## Run locally

From the `web` folder:

```bat
python -m http.server 8765
```

Open `http://127.0.0.1:8765/`. Do not open `index.html` as a file; the browser blocks modules that way.

## Cloudflare Pages

1. Push this repository, or upload the `web` folder.
2. Create a Pages project.
3. Set the build output directory to `web`.
4. Leave the build command empty.
5. Deploy. The site URL is the only thing users need.

## GitHub Pages

1. Push the repository.
2. Settings → Pages → Deploy from a branch.
3. If the site should live at `https://<user>.github.io/<repo>/`, either publish the `web` folder as the site root or add a `base` path. The simplest setup is a repository whose root is this `web` folder (or copy its contents to `docs/` and choose `docs` as the Pages folder).
4. Relative links (`css/app.css`, `js/main.js`, `assets/template.pdf`) work when this folder is the site root.

## Internal file share or IIS

Copy the `web` folder onto the share or the IIS site directory. Users open `index.html` through `http://` or `https://`, not as a double-clicked file.

No database, login, or upload URL is required. Do not put a Python app server in front of this site if the goal is to keep roster and LZ data off the server.
