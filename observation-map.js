// Display iNaturalist's public point tiles over the site's Web Mercator basemap.
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const WORLD = 4096;
  const WIDTH = 960;
  const HEIGHT = 520;
  const NORTH_AMERICA = [-170, 6, -49, 72];
  const SCRIPT = document.currentScript;
  const BASE = new URL("observation-basemap.svg#basemap", SCRIPT.src).href;
  const COUNT = "https://api.inaturalist.org/v2/observations";
  const PLACES = [
    ["Canada", -100, 56], ["United States", -99, 39], ["Mexico", -103, 23.5],
    ["Cuba", -80, 22], ["Hispaniola", -71.4, 18.6], ["Puerto Rico", -66.5, 18.1],
    ["Central America", -87.5, 14.7], ["Gulf of Mexico", -90, 25],
    ["British Columbia", -125, 54], ["Arizona", -111.9, 34.5], ["New Mexico", -106, 34.5],
    ["California", -120, 37], ["Texas", -99.5, 31], ["Florida", -82, 28],
    ["Sonora", -110.5, 29.5], ["Chihuahua", -106.4, 28.4], ["Sinaloa", -107.6, 25.2]
  ];

  function node(name, attrs) {
    const element = document.createElementNS(NS, name);
    for (const [attr, val] of Object.entries(attrs)) element.setAttribute(attr, val);
    return element;
  }

  function project(lon, lat) {
    const rad = Math.max(-83, Math.min(83, lat)) * Math.PI / 180;
    return [(lon + 180) / 360 * WORLD, (1 - Math.asinh(Math.tan(rad)) / Math.PI) / 2 * WORLD];
  }

  function windowFor([west, south, east, north]) {
    const [xmin, ymin] = project(west, north);
    const [xmax, ymax] = project(east, south);
    const scale = 1.12 * Math.max((xmax - xmin) / WIDTH, (ymax - ymin) / HEIGHT);
    const width = scale * WIDTH;
    const height = scale * HEIGHT;
    return {x: (xmin + xmax - width) / 2, y: (ymin + ymax - height) / 2, width, height, scale};
  }

  async function json(url, params) {
    const control = new AbortController();
    const timer = setTimeout(() => control.abort(), 12000);
    try {
      const response = await fetch(url + "?" + params, {signal: control.signal, credentials: "omit"});
      if (!response.ok) throw new Error("iNaturalist response unavailable");
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  async function resolveTaxon(element) {
    if (element.dataset.taxon) return Number(element.dataset.taxon);
    const name = element.dataset.name;
    const query = new URLSearchParams({q: name, rank: "species", is_active: "true", per_page: "20"});
    const {results} = await json("https://api.inaturalist.org/v1/taxa/autocomplete", query);
    const found = results.find(t => t.is_active && t.rank === "species" && t.name.toLowerCase() === name.toLowerCase());
    return found ? found.id : null;
  }

  function baseMap(svg, rect) {
    const {x, y, width, height, scale} = rect;
    svg.setAttribute("viewBox", [x, y, width, height].join(" "));
    svg.replaceChildren(node("use", {href: BASE}));
    const labels = node("g", {"aria-hidden": "true", "pointer-events": "none"});
    const boxes = [];
    for (const [label, lon, lat] of PLACES) {
      const [px, py] = project(lon, lat);
      const half = label.length * 3.7 * scale;
      if (px - half <= x || px + half >= x + width || py <= y + 18 * scale || py >= y + height - 9 * scale) continue;
      if (boxes.some(([ox, oy, ow]) => Math.abs(px - ox) < half + ow + 5 * scale && Math.abs(py - oy) < 20 * scale)) continue;
      const text = node("text", {x: px, y: py, "text-anchor": "middle", "font-size": 14 * scale,
        "font-family": "sans-serif", fill: "#50665b", stroke: "#fafaf2", "stroke-width": 2.5 * scale, "paint-order": "stroke"});
      text.textContent = label;
      labels.append(text);
      boxes.push([px, py, half]);
    }
    svg.append(labels);
  }

  function pointTiles(svg, rect, params, complete) {
    const z = Math.max(1, Math.min(9, Math.round(Math.log2(WORLD / (256 * rect.scale)))));
    const count = 2 ** z;
    const size = WORLD / count;
    const tiles = [];
    for (let col = Math.max(0, Math.floor(rect.x / size)); col < Math.min(count, Math.ceil((rect.x + rect.width) / size)); col++) {
      for (let row = Math.max(0, Math.floor(rect.y / size)); row < Math.min(count, Math.ceil((rect.y + rect.height) / size)); row++) {
        const src = "https://api.inaturalist.org/v1/points/" + z + "/" + col + "/" + row + ".png?" + params;
        tiles.push({col, row, src});
      }
    }
    let finished = 0;
    let failures = 0;
    const timer = setTimeout(() => complete(false), 14000);
    const done = ok => {
      if (!ok) failures++;
      if (++finished === tiles.length) {
        clearTimeout(timer);
        complete(failures === 0);
      }
    };
    for (const {col, row, src} of tiles) {
      const img = node("image", {x: size * col, y: size * row, width: size, height: size});
      img.addEventListener("load", () => done(true), {once:true});
      img.addEventListener("error", () => done(false), {once:true});
      img.setAttribute("href", src);
      svg.append(img);
    }
  }

  async function start(container) {
    const svg = container.querySelector("svg");
    const status = container.querySelector('[role="status"]');
    const button = container.querySelector("button");
    let id;
    try {
      id = await resolveTaxon(container);
    } catch {
      status.textContent = "The live iNaturalist map is temporarily unavailable. Open the record list below to check observations.";
      return;
    }
    if (!id) {
      status.textContent = "The species name could not be matched to an active iNaturalist taxon.";
      return;
    }
    const query = new URLSearchParams({taxon_id: String(id), place_id:"97394", quality_grade:"research", captive:"false", geo:"true"});
    const apiParams = new URLSearchParams(query);
    apiParams.set("per_page", "1");
    apiParams.set("fields", "id");
    const tileParams = new URLSearchParams(query);
    tileParams.set("color", "darkred");
    container.querySelector(".observation-link").href = "https://www.inaturalist.org/observations?" + query + "&view=map";
    let total = null;
    let ready = null;
    let continental = false;
    let revision = 0;

    function updateStatus() {
      if (total === 0) status.textContent = "iNaturalist currently returns no wild, research-grade records with public coordinates in North America.";
      else if (ready === false) status.textContent = "Some observation tiles could not load. Open the record list below to check coverage.";
      else if (ready === null) status.textContent = "Loading public observation coordinates…";
      else if (total === null) status.textContent = "Points show public coordinates of wild, research-grade observations in the current view.";
      else status.textContent = total.toLocaleString() + (total === 1 ? " matching North American record." : " matching North American records.") + " Points show public coordinates in the current view.";
    }
    function show() {
      const token = ++revision;
      const rect = windowFor(continental ? NORTH_AMERICA : container.dataset.bounds.split(",").map(Number));
      ready = null;
      baseMap(svg, rect);
      svg.removeAttribute("hidden");
      button.hidden = container.dataset.bounds === NORTH_AMERICA.join(",");
      button.textContent = continental ? "Show species region" : "Show North America";
      updateStatus();
      pointTiles(svg, rect, tileParams, ok => {
        if (revision !== token) return;
        ready = ok;
        updateStatus();
      });
    }
    button.addEventListener("click", () => { continental = !continental; show(); });
    show();
    try {
      const response = await json(COUNT, apiParams);
      if (Number.isInteger(response.total_results)) total = response.total_results;
    } catch {
      // Tiles can remain available independently of the count endpoint.
    }
    updateStatus();
  }

  const maps = document.querySelectorAll(".occurrence-view");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        start(entry.target);
      }
    }, {rootMargin: "160px"});
    maps.forEach(m => observer.observe(m));
  } else maps.forEach(start);
})();
