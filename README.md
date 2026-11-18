# North American Beetle Breeding

Choose **Log in** at the top right of any page and **Open the editor**. Use the GitHub owner account. Its linked Google account can be used on the GitHub sign-in screen. Repository write access controls publishing. Keep the repository and Pages CMS collaborator lists empty for single-owner access.

In **Species posts**, open a guide to change its text, choose **Add an entry** for a new guide, or use the entry menu to delete one. In **Photographs**, add an image, describe it for readers using a screen reader, and choose its life stage. Mark a preferred adult to use it as the lead photograph. Save the entry to publish it through the site's GitHub Pages workflow. Past versions can be recovered from GitHub's commit history.

Each post is stored in `guides/<slug>.json`. Its filename determines its permanent URL. Original photo credits and site-wide settings are in `catalog.json`. New photo uploads are stored in `uploads/`. The species list in the original catalogue is historical. Site pages, directories, search results and the sitemap are generated from the individual posts.

Run `python3 build.py --publish-dir ../public` to build the site in an empty output directory. Add new groups to `catalog.json` and update the family choices in `.pages.yml`.
