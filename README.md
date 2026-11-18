# North American Beetle Breeding

Open `index.html` to review the site locally. The family directory, species pages, photographs and species search work offline. Source links open the original publications and breeding accounts when online.

## Publish a species account

1. Open **Manage posts** in the website footer. Select an existing species to revise its page, or select **New species**.
2. Enter the scientific name, family or scarab subfamily, summary, life-history data and observations. Give each source a title and a URL. Use the classification fields for the corresponding BugGuide and iNaturalist pages.
3. To add photographs, enter each filename and its description under **Additional photographs**. Use distinct filenames for different photographs. Existing catalogue photographs stay available.
4. Choose **Download post file**, then **Sign in to GitHub and upload the post**. Upload the downloaded JSON file and any new photographs together. Use the repository owner's account, review the files and select **Commit changes**. GitHub publishes the revision after the Pages workflow finishes.

Editing an existing post keeps its URL. The published post automatically appears in its family, the species index and the sitemap. Visitors can prepare a draft locally. Only accounts with write access to the GitHub repository can publish.

## Local edits and new families

Keep downloaded `post-*.json` files and their photographs alongside `build.py`. Run `python3 build.py` from this folder to regenerate the HTML and search data. To build just the public site in a separate directory, run `python3 build.py --publish-dir ../public`.

To add a family or subfamily, copy an entry in the `groups` list in `catalog.json`. Enter its name, rank, stable slug, common name, overview and classification links. Rebuild the site. The new group will appear in the directory and the post editor. Existing posts with separate `post-*.json` files take precedence over the original catalogue records.
