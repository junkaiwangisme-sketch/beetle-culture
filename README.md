# Beetle Culture

A photographic, searchable beetle-breeding field guide. Visitors can browse a family or scarab subfamily, open a species guide, and follow the sources for each account.

## Add a species

Edit `catalog.json`. Copy a record in the `species` list and update these fields:

| Field | What to enter |
| --- | --- |
| `name` | Scientific name with genus capitalized and species lowercase |
| `slug` | A permanent URL name such as `dynastes-tityus` |
| `common` | An established English name, or an empty string |
| `group` | A slug from the `groups` list |
| `intro` | A short introduction to that species |
| `sections` | A list of objects with `title` and `text`, with husbandry observations attributed in the text where needed |
| `sources` | A list of objects with each source’s `title` and `url` |
| `aliases` | Optional list of searchable previous names or alternate common names |

Check the species index before adding a record. Add new observations to the existing record when the species already has a page. Preserve the guide’s slug so its URL stays stable.

## Add a photograph or family

Place each authorized, clearly identified photograph in the same directory as the catalog. Copy a similar entry in the catalog’s `photos` list. Match `species` to the guide’s scientific name, set `file`, and include the actual width, height, descriptive alt text, credit and source link. Record the license and its URL when applicable. The first photo listed for a species is its main guide image. Set `hero` to true on one high-resolution landscape photo for the homepage.

To add a family or scarab subfamily, copy a `groups` entry and edit its name, slug, rank, common name, and description. New species can then reference its slug.

## Build and preview

Run `python3 build.py` in this directory. The homepage, family directories, individual species pages, search index, photography credits, and sitemap all regenerate from the catalog. Open `index.html` in a browser to preview locally. The search works locally too.

For a GitHub Pages site published from the root of the main branch, commit the updated catalog, any photographs and all regenerated pages together. The catalog’s `url` controls absolute links in the sitemap and search metadata.
