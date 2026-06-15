const DATA_URL = "../game/game.json";

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

const HOST_NAMES = {
  raetian_frontier: "Raetian",
  marcomannia: "Marcomanni",
  quadi: "Quadi",
  iazyges: "Iazyges"
};
const HOST_LETTERS = {raetian_frontier: "R", marcomannia: "M", quadi: "Q", iazyges: "I"};
const TRACK_LABELS = ["rome", "senate", "resolve", "treasury", "supply", "fatigue", "mercy"];
const POSITIONS = {
  raetian_frontier: [35, 18], marcomannia: [52, 12], quadi: [70, 18], iazyges: [89, 29],
  aquileia: [9, 70], virunum: [27, 70], lauriacum: [45, 70], carnuntum: [64, 70], sirmium: [83, 70]
};
const PRIMARY_ROUTE = {
  raetian_frontier: "lauriacum", marcomannia: "lauriacum", quadi: "carnuntum",
  iazyges: "sirmium", sirmium: "carnuntum", carnuntum: "lauriacum",
  lauriacum: "virunum", virunum: "aquileia"
};

let data;
let spaces;
let fronts;
let state = null;
let mapMode = null;

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function clamp(value, low = 0, high = 7) {
  return Math.max(low, Math.min(high, value));
}

async function init() {
  const response = await fetch(DATA_URL);
  if (!response.ok) throw new Error(`Game data returned ${response.status}`);
  data = await response.json();
  spaces = Object.fromEntries(data.spaces.map(space => [space.id, space]));
  fronts = data.spaces.filter(space => space.kind === "front").map(space => space.id);
  $("#scenarioSelect").innerHTML = data.scenarios.map(scenario =>
    `<option value="${scenario.id}">${scenario.name} (${scenario.years}) — difficulty ${scenario.difficulty}</option>`
  ).join("");
  $("#startButton").addEventListener("click", startGame);
  $("#restartButton").addEventListener("click", () => location.reload());
  $("#rulesButton").addEventListener("click", showRules);
}

function buildCrisisDeck(scenario) {
  return scenario.groups.map(group => {
    const candidates = data.crises.filter(card => card.group === group);
    return {...candidates[Math.floor(Math.random() * candidates.length)]};
  });
}

function startGame() {
  const scenario = data.scenarios.find(item => item.id === $("#scenarioSelect").value);
  const commandDeck = shuffle(data.commands);
  state = {
    scenario,
    guided: $("#guidedToggle").checked,
    round: 0,
    phase: "start",
    tracks: {...scenario.tracks},
    strength: {...scenario.threat},
    hosts: {...scenario.hosts},
    legions: Object.fromEntries(data.spaces.map(space => [space.id, scenario.legions[space.id] || 0])),
    lostLegions: 0,
    momentum: 0,
    namedMomentum: Object.fromEntries(fronts.map(front => [front, 0])),
    commandDeck,
    commandDiscard: [],
    hand: [commandDeck.pop(), commandDeck.pop(), commandDeck.pop()],
    crisisDeck: buildCrisisDeck(scenario),
    crisis: null,
    commandUsed: false,
    basicOrders: [],
    fought: 0,
    meditated: false,
    assentUsed: false,
    freeCampaignBonus: 0,
    noFatigueBattle: false,
    clemencyBattle: false,
    addressTroops: false,
    gameOver: false,
    firstPetition: true,
    senateFiveAwarded: false,
    rainMiracleUsed: false,
    quadiCarnuntumPenalty: false,
    lockedSpace: null
  };
  $("#setupScreen").classList.add("hidden");
  $("#gameScreen").classList.remove("hidden");
  $("#restartButton").classList.remove("hidden");
  log(`<strong>${scenario.name}</strong> begins. ${scenario.history}`);
  beginRound();
}

async function beginRound() {
  if (state.gameOver) return;
  state.round += 1;
  state.phase = "crisis";
  state.commandUsed = false;
  state.basicOrders = [];
  state.fought = 0;
  state.meditated = false;
  state.assentUsed = false;
  state.freeCampaignBonus = 0;
  state.noFatigueBattle = false;
  state.clemencyBattle = false;
  state.addressTroops = false;
  state.lockedSpace = null;
  state.crisis = state.crisisDeck[state.round - 1];
  log(`<strong>Round ${state.round}:</strong> ${state.crisis.name}.`);
  render();
  await resolveArrival(state.crisis);
  if (checkImmediateLoss()) return;
  state.phase = "command";
  render();
}

async function resolveArrival(card) {
  const pressure = {...(card.pressure || {})};
  for (let [host, amount] of Object.entries(pressure)) {
    if (host === "highest") host = highestHost();
    changeStrength(host, amount);
  }
  if (card.id === "E02") {
    const choice = await choose("Eleven Envoys", "Pay for restraint, or exploit the embassy?", [
      {label: "Spend 1 Senate; reduce highest Strength by 1", value: "peace", disabled: state.tracks.senate < 1},
      {label: "Gain 1 Treasury; increase highest Strength by 1", value: "profit"}
    ]);
    if (choice === "peace") {
      changeTrack("senate", -1); changeStrength(highestHost(), -1);
    } else {
      changeTrack("treasury", 1); changeStrength(highestHost(), 1);
    }
  } else if (card.id === "E03") {
    const choice = await choose("The Plague Returns", "What does the epidemic consume?", [
      {label: "Lose 1 Rome", value: "rome"},
      {label: "Lose one Legion", value: "legion", disabled: totalLegions() < 1}
    ]);
    if (choice === "rome") changeTrack("rome", -1);
    else await removeLegionChoice("Choose the Legion lost to plague.");
  } else if (card.id === "E04") {
    changeTrack("resolve", -1);
    state.lockedSpace = await chooseSpace("Lucius Is Dead", "Choose a space whose Legions cannot March this round.", Object.keys(spaces));
  } else if (card.id === "E06") {
    changeTrack("rome", -1);
  } else if (card.id === "E08") {
    const choice = await choose("The Costoboci Raid South", "Pay for emergency defense?", [
      {label: "Pay 2 Treasury", value: "pay", disabled: state.tracks.treasury < 2},
      {label: "Lose 1 Rome and 1 Senate", value: "lose"}
    ]);
    if (choice === "pay") changeTrack("treasury", -2);
    else { changeTrack("rome", -1); changeTrack("senate", -1); }
  } else if (card.id === "E10") {
    const choice = await choose("The Rain and the Thirst", "What will the army surrender?", [
      {label: "Lose 2 Supply", value: "supply", disabled: state.tracks.supply < 2},
      {label: "Lose 1 Resolve", value: "resolve"}
    ]);
    changeTrack(choice, choice === "supply" ? -2 : -1);
  } else if (card.id === "E11" && state.tracks.senate >= 1) {
    const choice = await choose("Ariogaesus Defies Rome", "Spend Senate influence to contain the defiance?", [
      {label: "Spend 1 Senate; cancel the extra increase", value: "spend"},
      {label: "Accept the full mobilization", value: "accept"}
    ]);
    if (choice === "spend") {
      changeTrack("senate", -1);
      changeStrength("quadi", -1);
    } else changeStrength("quadi", 1);
  } else if (card.id === "E12") {
    const hostSpace = state.hosts.iazyges;
    if (state.legions[hostSpace] > 0) {
      const choice = await choose("Horsemen of the Iazyges", "Withdraw or let the horsemen gather?", [
        {label: "Move one Legion away", value: "move"},
        {label: "Increase Iazyges Strength by 1 more", value: "strength"}
      ]);
      if (choice === "move") await forcedMoveFrom(hostSpace);
      else changeStrength("iazyges", 1);
    } else changeStrength("iazyges", 1);
  } else if (card.id === "E13") {
    const choice = await choose("One Hundred Thousand Captives", "How will Rome frame the settlement?", [
      {label: "Gain 2 Rome", value: "rome"},
      {label: "Gain 1 Mercy; reduce Iazyges Strength by 1", value: "mercy"}
    ]);
    if (choice === "rome") changeTrack("rome", 2);
    else { changeTrack("mercy", 1); changeStrength("iazyges", -1); }
  } else if (card.id === "E14") {
    const choice = await choose("Cassius Takes the Purple", "Spend heavily to preserve Senate confidence?", [
      {label: "Spend 2 Treasury; lose 1 Senate", value: "pay", disabled: state.tracks.treasury < 2},
      {label: "Lose 2 Senate", value: "lose"}
    ]);
    if (choice === "pay") { changeTrack("treasury", -2); changeTrack("senate", -1); }
    else changeTrack("senate", -2);
  } else if (card.id === "E15") {
    const gain = await choose("Commodus at the Front", "What does the prince's presence secure?", [
      {label: "Gain 1 Rome", value: "rome"}, {label: "Gain 1 Senate", value: "senate"}
    ]);
    changeTrack(gain, 1);
    if (state.tracks.mercy < 3) changeTrack("resolve", -1);
  } else if (card.id === "E16") {
    const choice = await choose("Time Is a River", "Accept mortality or let the frontier gather?", [
      {label: "Lose 1 Resolve", value: "resolve"},
      {label: "Increase two lowest Strengths", value: "hosts"}
    ]);
    if (choice === "resolve") changeTrack("resolve", -1);
    else {
      const low = [...fronts].sort((a,b) => state.strength[a] - state.strength[b]).slice(0,2);
      low.forEach(host => changeStrength(host, 1));
    }
  }
  render();
}

function render() {
  renderScenario();
  renderTracks();
  renderMap();
  renderCrisis();
  renderCommands();
  renderActions();
  renderGuide();
}

function renderScenario() {
  const scenario = state.scenario;
  $("#scenarioKicker").textContent = `Round ${state.round} of ${scenario.rounds} · ${scenario.years}`;
  $("#scenarioName").textContent = scenario.name;
  $("#scenarioHistory").textContent = scenario.history;
  $("#scenarioRule").textContent = scenario.rule;
  const objective = scenario.objective;
  const parts = [`${state.momentum}/${objective.momentum} Momentum`];
  if (objective.max_total_threat != null) parts.push(`Strength ${totalStrength()}/${objective.max_total_threat} max`);
  if (objective.mercy) parts.push(`Mercy ${state.tracks.mercy}/${objective.mercy}`);
  if (objective.senate) parts.push(`Senate ${state.tracks.senate}/${objective.senate}`);
  if (objective.resolve) parts.push(`Resolve ${state.tracks.resolve}/${objective.resolve}`);
  if (objective.named) {
    for (const [host, target] of Object.entries(objective.named)) {
      parts.push(`${HOST_NAMES[host]} victories ${state.namedMomentum[host]}/${target}`);
    }
  }
  $("#objective").textContent = `Objective: ${parts.join(" · ")}`;
  $("#phaseBadge").textContent = phaseName();
}

function renderTracks() {
  const extra = [["momentum", state.momentum], ["lost legions", state.lostLegions]];
  $("#tracks").innerHTML = [
    ...TRACK_LABELS.map(key => [key, state.tracks[key]]), ...extra
  ].map(([label, value]) => `<div class="track"><strong>${value}</strong><span>${label}</span></div>`).join("");
}

function renderMap() {
  const routePairs = [];
  for (const space of data.spaces) {
    for (const neighbor of space.adjacent) {
      if (space.id < neighbor) routePairs.push([space.id, neighbor]);
    }
  }
  const routes = routePairs.map(([a,b]) => routeHtml(a,b)).join("");
  const nodes = data.spaces.map(space => {
    const [x,y] = POSITIONS[space.id];
    const legionCount = state.legions[space.id] || 0;
    const hostIds = fronts.filter(host => state.hosts[host] === space.id && state.strength[host] > 0);
    const treatyIds = fronts.filter(host => state.hosts[host] === space.id && state.strength[host] === 0);
    const selectable = mapMode?.allowed?.includes(space.id);
    const pieces = [
      ...Array.from({length: legionCount}, () => `<span class="legion" title="Roman Legion">L</span>`),
      ...hostIds.map(host => `<span class="host ${host}" title="${HOST_NAMES[host]} Host">${HOST_LETTERS[host]}</span>`),
      ...treatyIds.map(host => `<span class="host ${host} pacified" title="${HOST_NAMES[host]} treaty">${HOST_LETTERS[host]}</span>`)
    ].join("");
    const strength = space.kind === "front"
      ? `<div class="strength">${HOST_NAMES[space.id]} Strength ${state.strength[space.id]}</div>` : "";
    return `<button class="space ${space.kind} ${selectable ? "selectable" : ""}" data-space="${space.id}"
      style="left:${x}%;top:${y}%">
      <h4>${space.name}</h4><div class="pieces">${pieces || `<span class="muted">empty</span>`}</div>${strength}
    </button>`;
  }).join("");
  $("#map").innerHTML = routes + nodes;
  $$("#map .space").forEach(button => button.addEventListener("click", () => handleMapClick(button.dataset.space)));
  $("#mapPrompt").textContent = mapMode?.prompt || "";
}

function routeHtml(a,b) {
  const [x1,y1] = POSITIONS[a], [x2,y2] = POSITIONS[b];
  const dx = x2 - x1, dy = y2 - y1;
  const width = Math.sqrt(dx*dx + dy*dy);
  const angle = Math.atan2(dy, dx) * 180 / Math.PI;
  const invasion = PRIMARY_ROUTE[a] === b || PRIMARY_ROUTE[b] === a;
  return `<div class="route ${invasion ? "invasion" : ""}" style="left:${x1}%;top:${y1}%;width:${width}%;transform:rotate(${angle}deg)"></div>`;
}

function renderCrisis() {
  if (!state.crisis) return;
  const host = state.crisis.host === "highest" ? "Highest Host" : `${HOST_NAMES[state.crisis.host]} Host`;
  $("#crisisCard").innerHTML = `<div class="crisis-card">
    <div><p class="eyebrow">${state.crisis.id} · Group ${state.crisis.group}</p>
    <h3>${state.crisis.name}</h3><p><strong>Arrival:</strong> ${state.crisis.arrival}</p>
    <p><strong>Design:</strong> ${state.crisis.design}</p></div>
    <div class="order">${host}: ${state.crisis.order}</div>
  </div>`;
}

function renderCommands() {
  $("#deckCount").textContent = `${state.commandDeck.length} cards in deck`;
  $("#commandHand").innerHTML = state.hand.map(card => `<article class="command-card ${state.phase !== "command" ? "disabled" : ""}">
    <header><p class="eyebrow">${card.id} · ${card.tag}</p><h4>${card.name}</h4></header>
    <button class="command-side" data-card="${card.id}" data-side="imperium"><strong>IMPERIUM</strong><span>${card.imperium}</span></button>
    <button class="command-side" data-card="${card.id}" data-side="officium"><strong>OFFICIUM</strong><span>${card.officium}</span></button>
  </article>`).join("");
  $$(".command-side").forEach(button => button.addEventListener("click", () => useCommand(button.dataset.card, button.dataset.side)));
}

function renderActions() {
  const box = $("#actionButtons");
  box.innerHTML = "";
  if (state.gameOver) return;
  if (state.phase === "crisis") {
    $("#actionTitle").textContent = "Receive the Crisis";
    $("#actionText").textContent = "Applying the event...";
  } else if (state.phase === "command") {
    $("#actionTitle").textContent = "Choose one Command half";
    $("#actionText").textContent = "Use Imperium for the frontier or Officium for Rome. The other half is lost.";
  } else if (state.phase === "orders") {
    $("#actionTitle").textContent = `Basic Orders (${state.basicOrders.length}/2)`;
    $("#actionText").textContent = "Choose two different orders. Map selections will be highlighted.";
    const orders = [
      ["March", startMarch, canMarch()],
      ["Fortify", startFortify, canFortify()],
      ["Campaign", startCampaign, canCampaign()],
      ["Petition", petition, true],
      ["Requisition", requisition, true],
      ["Meditate", meditate, true]
    ];
    for (const [label, fn, allowed] of orders) {
      const button = document.createElement("button");
      button.className = "secondary";
      button.textContent = label;
      button.disabled = !allowed || state.basicOrders.includes(label.toLowerCase());
      button.addEventListener("click", fn);
      box.append(button);
    }
    if (state.basicOrders.length === 2) {
      const end = document.createElement("button");
      end.className = "primary";
      end.textContent = "Resolve Enemy Design";
      end.addEventListener("click", resolveEnemyDesign);
      box.append(end);
    }
  } else if (state.phase === "enemy") {
    $("#actionTitle").textContent = "Enemy Design";
    $("#actionText").textContent = "One Host acts. All other opposition remains still.";
  }
}

function renderGuide() {
  if (!state.guided) {
    $("#guide").classList.add("hidden");
    return;
  }
  $("#guide").classList.remove("hidden");
  const messages = {
    crisis: ["Receive", "The Crisis reveals both the historical event and the Host order that will resolve after your actions."],
    command: ["Deliberate", "Choose one half of one Command card. This is your strongest action this round."],
    orders: ["Issue Orders", "Choose two different Basic Orders. Reposition before the visible Host order resolves."],
    enemy: ["Enemy Design", "Only the named Host acts: it Musters or Raids one connection toward Aquileia."]
  };
  const [title, text] = messages[state.phase] || ["Endure", "The result is now part of the campaign."];
  $("#guide").innerHTML = `<strong>${title}.</strong> ${text}`;
}

async function useCommand(id, side) {
  if (state.phase !== "command") return;
  const card = state.hand.find(item => item.id === id);
  if (!card) return;
  await resolveCommand(card, side);
  state.lastCommandId = card.id;
  state.lastCommandSide = side;
  state.hand = state.hand.filter(item => item.id !== id);
  state.commandDiscard.push(card);
  drawCommand();
  state.commandUsed = true;
  state.phase = "orders";
  log(`Used <strong>${card.name}</strong> for ${side === "imperium" ? "Imperium" : "Officium"}.`);
  render();
}

async function resolveCommand(card, side) {
  const id = card.id;
  if (side === "officium") {
    if (id === "C01") { changeTrack("senate", 1); await moveTowardAquileia(); }
    else if (id === "C02") { changeTrack("supply", 2); changeTrack("treasury", -1); }
    else if (id === "C03") { changeTrack("senate", 1); changeTrack("fatigue", -1); }
    else if (id === "C04") { changeTrack("treasury", 4); changeTrack("rome", -1); }
    else if (id === "C05") await raiseLegion(true);
    else if (id === "C06") { changeTrack("rome", 2); changeTrack("treasury", -1); }
    else if (id === "C07") {
      if (state.tracks.senate >= 1) {
        changeTrack("senate", -1);
        const host = await chooseHost("Divide the Coalition", "Choose a Host to weaken.");
        changeStrength(host, -1); changeTrack("mercy", 1);
      }
    } else if (id === "C08") { changeTrack("supply", 1); changeTrack("resolve", 1); }
    else if (id === "C09") {
      changeTrack("resolve", 1); changeTrack("supply", 1); changeTrack("senate", 1); changeStrength(highestHost(), 1);
    } else if (id === "C10") {
      changeTrack("resolve", 2); if (state.tracks.mercy < 3) changeTrack("senate", -1);
    } else if (id === "C11") {
      if (totalStrength() <= 8) changeTrack("senate", 2); else changeTrack("treasury", 1);
    } else if (id === "C12") { changeTrack("rome", 1); changeTrack("mercy", 1); changeTrack("treasury", -1); }
    else if (id === "C13") {
      const resource = await choose("Danube Fleet", "Choose the fleet's civil benefit.", [
        {label: "Gain 2 Supply", value: "supply"}, {label: "Gain 1 Treasury", value: "treasury"}
      ]);
      changeTrack(resource, resource === "supply" ? 2 : 1);
    } else if (id === "C14") {
      const next = state.crisisDeck.slice(state.round, state.round + 3).map(c => c.name).join(" → ");
      await notice("Council at Carnuntum", next ? `Coming Crises: ${next}` : "No later Crises remain.");
    } else if (id === "C15") { changeTrack("resolve", 1); await petition(true); }
    else if (id === "C16" && state.tracks.senate >= 1) {
      changeTrack("senate", -1); changeTrack("mercy", 1); changeTrack("rome", 1); changeTrack("resolve", 1);
    }
  } else {
    if (id === "C01") await specialMarch(2, 2);
    else if (id === "C02") {
      if (state.tracks.supply >= 1) {
        changeTrack("supply", -1);
        const first = await chooseHost("Secure the River", "Choose the first Host."); changeStrength(first, -1);
        const second = await chooseHost("Secure the River", "Choose the second Host.", [first]); changeStrength(second, -1);
      }
    } else if (id === "C03") { state.freeCampaignBonus = 2; await campaign(true); }
    else if (id === "C04") { changeTrack("treasury", 3); await campaign(true); }
    else if (id === "C05") await raiseLegion(false);
    else if (id === "C06" && state.tracks.supply >= 1) {
      changeTrack("supply", -1);
      const host = await choose("Fortify Italy", "Choose a Host.", [
        {label: "Raetian", value: "raetian_frontier"}, {label: "Marcomanni", value: "marcomannia"}
      ]);
      changeStrength(host, -2);
    } else if (id === "C07") {
      const down = await chooseHost("Divide the Coalition", "Reduce which Host by 2?");
      const up = await chooseHost("Divide the Coalition", "Increase which other Host?", [down]);
      changeStrength(down, -2); changeStrength(up, 1);
    } else if (id === "C08") await specialMarch(3, 2);
    else if (id === "C09") { changeTrack("fatigue", -2); await fortify(true); }
    else if (id === "C10") { state.addressTroops = true; await campaign(true); }
    else if (id === "C11") { state.freeCampaignBonus = 0; await campaign(true, {hostages: true}); }
    else if (id === "C12") {
      const eligible = fronts.filter(host => state.strength[host] <= 2 && state.momentum >= 1);
      if (eligible.length) {
        const host = await chooseHost("Return the Prisoners", "Choose a Host to settle.", fronts.filter(h => !eligible.includes(h)));
        state.momentum -= 1; state.strength[host] = 0; state.hosts[host] = host; changeTrack("mercy", 2);
      }
    } else if (id === "C13") { await fleetMove(); state.freeCampaignBonus = 1; }
    else if (id === "C14") {
      const next = state.crisisDeck.slice(state.round, state.round + 2).map(c => c.name).join(" → ");
      await notice("Council at Carnuntum", next ? `Next Crises: ${next}` : "No later Crises remain.");
      await fortify(true);
    } else if (id === "C15") { state.noFatigueBattle = true; await campaign(true); }
    else if (id === "C16") { state.clemencyBattle = true; await campaign(true); }
  }
}

function drawCommand() {
  if (!state.commandDeck.length) {
    state.commandDeck = shuffle(state.commandDiscard);
    state.commandDiscard = [];
    changeTrack("fatigue", 1);
    log("The Command deck reshuffles; administrative fatigue rises.");
  }
  if (state.commandDeck.length) state.hand.push(state.commandDeck.pop());
}

function addBasicOrder(name) {
  if (!state.basicOrders.includes(name)) state.basicOrders.push(name);
  mapMode = null;
  render();
}

function canMarch() { return Object.values(state.legions).some(count => count > 0); }
function canFortify() { return fronts.some(host => eligibleFortify(host)); }
function canCampaign() { return fronts.some(host => state.strength[host] > 0 && state.legions[state.hosts[host]] > 0); }

function startMarch() {
  const allowed = Object.keys(spaces).filter(id => state.legions[id] > 0 && id !== state.lockedSpace);
  mapMode = {type: "march-source", allowed, prompt: "Choose a space containing the Legion you want to move."};
  renderMap();
}

function startFortify() { fortify(false); }
function startCampaign() { campaign(false); }

async function handleMapClick(spaceId) {
  if (!mapMode?.allowed?.includes(spaceId)) return;
  if (mapMode.type === "march-source") {
    const destinations = spaces[spaceId].adjacent;
    mapMode = {type: "march-destination", source: spaceId, allowed: destinations, prompt: `Move from ${spaces[spaceId].name} to which adjacent space?`};
    renderMap();
  } else if (mapMode.type === "march-destination") {
    const source = mapMode.source;
    const max = Math.min(2, state.legions[source]);
    const count = max === 1 ? 1 : Number(await choose("March", "How many Legions move?", [
      {label: "Move 1 Legion", value: "1"}, {label: "Move 2 Legions", value: "2"}
    ]));
    moveLegions(source, spaceId, count);
    addBasicOrder("march");
  }
}

async function specialMarch(capacity, range) {
  const source = await chooseSpace("Special March", `Choose a source with up to ${capacity} Legions.`, Object.keys(spaces).filter(id => state.legions[id] > 0));
  const reachable = reachableWithin(source, range).filter(id => id !== source);
  const destination = await chooseSpace("Special March", "Choose the destination.", reachable);
  const options = Array.from({length: Math.min(capacity, state.legions[source])}, (_,i) => ({label: `Move ${i+1}`, value: String(i+1)}));
  const count = Number(await choose("Special March", "How many Legions?", options));
  moveLegions(source, destination, count);
  if (capacity === 3) changeTrack("fatigue", 1);
}

async function fortify(free) {
  const eligible = fronts.filter(eligibleFortify);
  if (!eligible.length) return notice("Fortify", "No Host is within reach of your Legions.");
  if (!free && state.tracks.supply < 1) return notice("Fortify", "You need 1 Supply.");
  const host = await chooseHost("Fortify", "Choose the Host whose Strength is reduced.", fronts.filter(h => !eligible.includes(h)));
  if (!free) changeTrack("supply", -1);
  changeStrength(host, -1);
  if (!free) addBasicOrder("fortify");
}

function eligibleFortify(host) {
  const hostSpace = state.hosts[host];
  return state.strength[host] > 0 && (
    state.legions[hostSpace] > 0 ||
    spaces[hostSpace].adjacent.some(id => spaces[id].kind === "base" && state.legions[id] > 0)
  );
}

async function campaign(free, options = {}) {
  const eligible = fronts.filter(host => state.strength[host] > 0 && state.legions[state.hosts[host]] > 0);
  if (!eligible.length) return notice("Campaign", "No Host shares a space with a Legion.");
  const host = await chooseHost("Campaign", "Choose the Host to battle.", fronts.filter(h => !eligible.includes(h)));
  if (state.scenario.id === "S06" && state.tracks.treasury < 1) return notice("Campaign", "This scenario requires 1 Treasury per Campaign.");
  if (state.scenario.id === "S06") changeTrack("treasury", -1);
  await resolveBattle(host, false, options);
  if (!free) addBasicOrder("campaign");
}

async function resolveBattle(host, clash = false, options = {}) {
  const space = state.hosts[host];
  const available = state.legions[space];
  if (!available) return;
  const choices = Array.from({length: available}, (_,i) => ({label: `Commit ${i+1} Legion${i ? "s" : ""}`, value: String(i+1)}));
  const committed = Number(await choose(clash ? "Clash" : "Campaign", `${HOST_NAMES[host]} Strength ${state.strength[host]}.`, choices));
  const supplyCost = clash ? 0 : Math.max(0, committed - 1);
  if (state.tracks.supply < supplyCost) return notice("Insufficient Supply", `You need ${supplyCost} Supply.`);
  if (supplyCost) changeTrack("supply", -supplyCost);
  let exert = false;
  if (!clash && state.tracks.fatigue < 6) {
    exert = await choose("Exertion", "Add +2 Roman total and gain 1 Fatigue?", [
      {label: "Fight without Exertion", value: "no"}, {label: "Exert the army", value: "yes"}
    ]) === "yes";
  }
  let romanDie = d6(), enemyDie = d6();
  const baseSupport = spaces[space].kind === "base" || spaces[space].adjacent.some(id => spaces[id].kind === "base" && state.legions[id] > 0);
  let bonus = (baseSupport ? 1 : 0) + state.freeCampaignBonus + (exert ? 2 : 0);
  if (state.scenario.id === "S03" && host === "marcomannia") bonus += 1;
  if (state.crisis?.id === "E09" && ["quadi","iazyges"].includes(host)) bonus += 1;
  if (state.crisis?.id === "E15" && !clash) bonus += 1;
  let enemyBonus = state.scenario.id === "S05" && host === "iazyges" && committed < 3 ? 1 : 0;
  if (state.crisis?.id === "E12" && host === "iazyges") enemyBonus += 1;
  let roman = committed + romanDie + bonus;
  let enemy = state.strength[host] + enemyDie + enemyBonus;
  let margin = roman - enemy;
  if (exert) changeTrack("fatigue", 1);

  if (
    !clash &&
    state.scenario.id === "S04" &&
    margin < 0 &&
    !state.rainMiracleUsed &&
    state.tracks.treasury >= 1
  ) {
    const invokeRain = await choose("The Rain Miracle",
      "The battle is turning against Rome. Spend 1 Treasury to set both battle dice to 4?", [
        {label: "Invoke the miracle", value: "yes"},
        {label: "Accept the result", value: "no"}
      ]) === "yes";
    if (invokeRain) {
      state.rainMiracleUsed = true;
      changeTrack("treasury", -1);
      romanDie = 4;
      enemyDie = 4;
      roman = committed + romanDie + bonus;
      enemy = state.strength[host] + enemyDie + enemyBonus;
      margin = roman - enemy;
      log("Rain breaks over the battlefield. Both dice become 4.");
    }
  }

  await showDice(clash ? "Clash" : "Battle", romanDie, enemyDie,
    `Rome ${roman} vs ${HOST_NAMES[host]} ${enemy}. Margin ${margin >= 0 ? "+" : ""}${margin}.`);
  if (clash) {
    if (margin > 0) { changeStrength(host, -1); retreatHost(host, false); log(`The ${HOST_NAMES[host]} Host is repulsed toward home.`); }
    else if (margin === 0) log("The Clash ends with both forces holding.");
    else if (margin >= -2) changeTrack("resolve", -1);
    else { removeLegions(space, 1); changeTrack("rome", -1); }
  } else {
    state.fought += 1;
    if (margin >= 3) {
      changeStrength(host, options.hostages ? -3 : -2);
      retreatHost(host, true);
      gainMomentum(host, state.clemencyBattle);
      if (options.hostages) changeTrack("mercy", -1);
    } else if (margin >= 1) {
      changeStrength(host, options.hostages ? -2 : -1);
      retreatHost(host, false);
      gainMomentum(host, state.clemencyBattle);
      if (options.hostages) changeTrack("mercy", -1);
    } else if (margin === 0) {
      changeStrength(host, -1);
      const cost = await choose("Battle Tied", "Choose the cost of holding the field.", [
        {label: "Lose 1 Supply", value: "supply", disabled: state.tracks.supply < 1},
        {label: "Gain 1 Fatigue", value: "fatigue"}
      ]);
      changeTrack(cost, cost === "fatigue" ? 1 : -1);
    } else if (margin >= -2) {
      changeTrack("supply", -1); changeTrack("resolve", -1);
      if (state.addressTroops) changeTrack("resolve", 1);
    } else {
      removeLegions(space, 1); changeTrack("rome", -1);
      if (state.addressTroops) changeTrack("resolve", 1);
    }
  }
  state.freeCampaignBonus = 0;
  state.addressTroops = false;
  state.clemencyBattle = false;
  if (!state.assentUsed && margin < 3) {
    const assentUsed = await offerAssent();
    if (assentUsed && state.crisis?.id === "E10") {
      changeStrength(host, -1);
      log("The Senate's censure weakens the battled Host by 1 Strength.");
    }
  }
  render();
}

function gainMomentum(host, clemency) {
  if (clemency) {
    changeTrack("mercy", 1); changeTrack("fatigue", -1);
  } else {
    state.momentum += 1;
    state.namedMomentum[host] += 1;
  }
}

async function offerAssent() {
  const choice = await choose("Stoic Assent", "Accept the unmodified result and preserve an inner resource?", [
    {label: "Gain 1 Resolve", value: "resolve"}, {label: "Gain 1 Mercy", value: "mercy"},
    {label: "Do not use Assent", value: "none"}
  ]);
  if (choice !== "none") {
    changeTrack(choice, 1);
    state.assentUsed = true;
    return true;
  }
  return false;
}

async function petition(free = false) {
  const negotiable = fronts.filter(host =>
    state.strength[host] <= 1 && state.hosts[host] === host && state.legions[host] > 0
  );
  if (negotiable.length) {
    const choice = await choose("Petition or Negotiate", "Use political capacity in Rome or seek peace?", [
      {label: "Gain 1 Senate", value: "petition"},
      {label: "Negotiate with a Host", value: "negotiate"}
    ]);
    if (choice === "negotiate") {
      const host = await chooseHost("Negotiate", "Choose the people offered peace.", fronts.filter(h => !negotiable.includes(h)));
      const resource = await choose("Price of Peace", "Pay Senate or Treasury.", [
        {label: "Spend 1 Senate", value: "senate", disabled: state.tracks.senate < 1},
        {label: "Spend 1 Treasury", value: "treasury", disabled: state.tracks.treasury < 1}
      ]);
      changeTrack(resource, -1); state.strength[host] = 0; state.hosts[host] = host; changeTrack("mercy", 1);
      log(`A treaty is made with the ${HOST_NAMES[host]}.`);
    } else {
      if (!free && !(state.scenario.id === "S01" && state.firstPetition)) {
        if (state.tracks.treasury < 1) return notice("Petition", "You need 1 Treasury.");
        changeTrack("treasury", -1);
      }
      changeTrack("senate", 1); state.firstPetition = false;
    }
  } else {
    if (!free && !(state.scenario.id === "S01" && state.firstPetition)) {
      if (state.tracks.treasury < 1) return notice("Petition", "You need 1 Treasury.");
      changeTrack("treasury", -1);
    }
    changeTrack("senate", 1); state.firstPetition = false;
  }
  if (!free) addBasicOrder("petition");
}

async function requisition() {
  const loss = await choose("Requisition", "Where does forced supply fall hardest?", [
    {label: "Lose 1 Rome", value: "rome"}, {label: "Lose 1 Senate", value: "senate"}
  ]);
  changeTrack("supply", state.crisis?.id === "E06" ? 3 : 2);
  changeTrack(loss, -1);
  addBasicOrder("requisition");
}

function meditate() {
  changeTrack("resolve", 1);
  state.meditated = true;
  addBasicOrder("meditate");
}

async function resolveEnemyDesign() {
  state.phase = "enemy";
  render();
  const card = state.crisis;
  if (card.id === "E04" && state.commandUsed && state.lastCommandSide === "officium") changeTrack("senate", 1);
  if (card.id === "E06" && !state.basicOrders.includes("campaign") && !state.basicOrders.includes("fortify")) changeTrack("senate", -1);
  if (card.id === "E07" && state.lastCommandId === "C07") {
    const host = await chooseHost("Diplomatic Division", "Reduce a different Host by 1.");
    changeStrength(host, -1);
  }
  if (card.id === "E09" && state.fought) changeTrack("fatigue", 1);
  if (card.id === "E11" && state.strength.quadi <= 1) state.momentum += 1;
  if (card.id === "E13" && state.strength.iazyges > 0) changeTrack("supply", -1);
  if (card.id === "E14" && state.tracks.senate <= 2) changeTrack("rome", -1);
  await activateHost(card);
  await endure();
}

async function activateHost(card) {
  let host = card.host === "highest" ? highestHost() : card.host;
  if (state.strength[host] === 0) {
    state.strength[host] = 1;
    state.hosts[host] = host;
    log(`The treaty with the ${HOST_NAMES[host]} breaks; the Host returns at Strength 1.`);
    return;
  }
  if (card.order === "muster" && state.strength[host] < 6) {
    changeStrength(host, 1);
    log(`The ${HOST_NAMES[host]} Host musters to Strength ${state.strength[host]}.`);
    return;
  }
  const current = state.hosts[host];
  if (state.legions[current] > 0) {
    log(`The ${HOST_NAMES[host]} Host attacks at ${spaces[current].name}.`);
    await resolveBattle(host, true);
    if (current === "aquileia" && state.hosts[host] === "aquileia") return loseGame("Aquileia falls.");
    return;
  }
  const destination = PRIMARY_ROUTE[current];
  if (!destination) return;
  state.hosts[host] = destination;
  log(`The ${HOST_NAMES[host]} Host raids from ${spaces[current].name} to ${spaces[destination].name}.`);
  if (
    state.scenario.id === "S02" &&
    host === "quadi" &&
    destination === "carnuntum" &&
    !state.quadiCarnuntumPenalty
  ) {
    state.quadiCarnuntumPenalty = true;
    changeTrack("rome", -1);
    log("The Quadi enter Carnuntum: lose 1 Rome.");
  }
  if (state.legions[destination] > 0) {
    await resolveBattle(host, true);
    if (destination === "aquileia" && state.hosts[host] === "aquileia") loseGame("Aquileia falls.");
  } else if (destination === "aquileia") {
    loseGame("The road to Aquileia lies open.");
  } else if (spaces[destination].kind === "base") {
    changeTrack("rome", -1);
    const resource = await choose(`${spaces[destination].name} Raided`, "What else is lost?", [
      {label: "Lose 1 Supply", value: "supply"}, {label: "Lose 1 Treasury", value: "treasury"}
    ]);
    changeTrack(resource, -1);
  }
}

async function endure() {
  if (state.gameOver) return;
  if (state.fought && !state.noFatigueBattle) changeTrack("fatigue", state.fought);
  if (state.meditated && !state.fought) changeTrack("fatigue", -1);
  if (state.tracks.fatigue >= 5) changeTrack("resolve", -1);
  if (state.scenario.id === "S07" && [4,7].includes(state.round) && !state.meditated) changeTrack("resolve", -1);
  if (state.scenario.id === "S08") {
    if ([3,6].includes(state.round)) { changeTrack("fatigue", -1); changeStrength(highestHost(), 1); }
    if (state.round === 8) changeTrack("resolve", -1);
  }
  state.noFatigueBattle = false;
  if (checkImmediateLoss()) return;
  if (state.round >= state.scenario.rounds) return finishScenario();
  await beginRound();
}

function finishScenario() {
  const won = objectiveMet();
  const score = state.momentum + state.tracks.rome + state.tracks.senate + state.tracks.resolve +
    state.tracks.treasury - state.tracks.fatigue - totalStrength();
  state.gameOver = true;
  state.phase = "end";
  const title = won ? "The frontier endures" : "The burden exceeds the state";
  const grade = won ? (score >= 18 ? "Decisive" : score >= 12 ? "Hard Peace" : "Pyrrhic Duty") : "Defeat";
  showEnd(title, `${grade}. Final score ${score}.`);
}

function objectiveMet() {
  const o = state.scenario.objective;
  if (state.momentum < (o.momentum || 0)) return false;
  if (o.max_total_threat != null && totalStrength() > o.max_total_threat) return false;
  if (o.senate && state.tracks.senate < o.senate) return false;
  if (o.resolve && state.tracks.resolve < o.resolve) return false;
  if (o.mercy && state.tracks.mercy < o.mercy) return false;
  if (o.named && Object.entries(o.named).some(([host,target]) => state.namedMomentum[host] < target)) return false;
  return !Object.values(state.hosts).includes("aquileia");
}

function checkImmediateLoss() {
  if (state.tracks.rome <= 0) return loseGame("Rome loses confidence in the war.");
  if (state.tracks.senate <= 0) return loseGame("The imperial government fractures.");
  if (state.tracks.resolve <= 0) return loseGame("Marcus can no longer bear the office.");
  if (totalLegions() <= 0) return loseGame("No field army remains.");
  return false;
}

function loseGame(reason) {
  if (state.gameOver) return true;
  state.gameOver = true;
  state.phase = "end";
  showEnd("Defeat", reason);
  return true;
}

function showEnd(title, text) {
  render();
  $("#modalContent").innerHTML = `<div class="modal-inner"><p class="eyebrow">Campaign complete</p><h2>${title}</h2>
    <p>${text}</p><div class="modal-actions"><button class="primary" onclick="location.reload()">New campaign</button></div></div>`;
  $("#modal").showModal();
}

function highestHost() {
  return [...fronts].sort((a,b) => {
    const strength = state.strength[b] - state.strength[a];
    if (strength) return strength;
    return routeToAquileia(state.hosts[a]).length - routeToAquileia(state.hosts[b]).length;
  })[0];
}

function routeToAquileia(start) {
  const path = [start];
  let current = start;
  while (current !== "aquileia" && PRIMARY_ROUTE[current]) {
    current = PRIMARY_ROUTE[current];
    path.push(current);
  }
  return path;
}

function route(start, goal) {
  const queue = [[start]], seen = new Set([start]);
  while (queue.length) {
    const path = queue.shift();
    if (path.at(-1) === goal) return path;
    for (const neighbor of spaces[path.at(-1)].adjacent) {
      if (!seen.has(neighbor)) { seen.add(neighbor); queue.push([...path, neighbor]); }
    }
  }
  return [start];
}

function reachableWithin(start, distance) {
  return Object.keys(spaces).filter(id => route(start,id).length - 1 <= distance);
}

function retreatHost(host, decisive) {
  const current = state.hosts[host];
  if (current === host) return;
  const path = route(current, host);
  state.hosts[host] = decisive ? host : path[1];
}

function moveLegions(source, destination, count) {
  count = Math.min(count, state.legions[source]);
  state.legions[source] -= count;
  state.legions[destination] += count;
  for (const host of fronts) {
    if (host === source && state.strength[host] === 0 && state.legions[source] === 0) {
      state.strength[host] = 1;
      log(`The ${HOST_NAMES[host]} treaty breaks as its garrison leaves.`);
    }
  }
  log(`${count} Legion${count === 1 ? "" : "s"} march from ${spaces[source].name} to ${spaces[destination].name}.`);
}

async function forcedMoveFrom(source) {
  const destination = await chooseSpace("Withdraw", "Choose an adjacent destination.", spaces[source].adjacent);
  moveLegions(source, destination, 1);
}

async function fleetMove() {
  const source = state.legions.carnuntum ? "carnuntum" : "sirmium";
  const destination = source === "carnuntum" ? "sirmium" : "carnuntum";
  if (!state.legions[source]) return notice("Danube Fleet", "No Legions are available at Carnuntum or Sirmium.");
  const options = Array.from({length: state.legions[source]}, (_,i) => ({label: `Move ${i+1}`, value: String(i+1)}));
  const count = Number(await choose("Danube Fleet", `${source} to ${destination}`, options));
  moveLegions(source, destination, count);
}

async function moveTowardAquileia() {
  const candidates = Object.keys(spaces).filter(id => state.legions[id] > 0 && id !== "aquileia");
  if (!candidates.length) return;
  const source = await chooseSpace("Recall a Legion", "Choose its current space.", candidates);
  const path = route(source, "aquileia");
  moveLegions(source, path[1], 1);
}

async function raiseLegion(officium) {
  const treasury = officium ? 2 : 3;
  const senate = officium ? 1 : 0;
  if (!state.lostLegions || state.tracks.treasury < treasury || state.tracks.senate < senate) {
    return notice("Raise New Legions", "You lack a lost Legion or the required political resources.");
  }
  changeTrack("treasury", -treasury);
  changeTrack("senate", -senate);
  state.lostLegions -= 1;
  state.legions.aquileia += 1;
  if (officium) changeTrack("rome", 1);
}

function removeLegions(space, count) {
  const removed = Math.min(count, state.legions[space]);
  state.legions[space] -= removed;
  state.lostLegions += removed;
}

async function removeLegionChoice(title) {
  const spacesWithLegions = Object.keys(spaces).filter(id => state.legions[id] > 0);
  const space = await chooseSpace("Legion Loss", title, spacesWithLegions);
  removeLegions(space, 1);
}

function changeTrack(track, amount) {
  const max = track === "fatigue" || track === "mercy" ? 6 : 7;
  state.tracks[track] = clamp(state.tracks[track] + amount, 0, max);
  if (
    track === "senate" &&
    state.scenario.id === "S06" &&
    state.tracks.senate >= 5 &&
    !state.senateFiveAwarded
  ) {
    state.senateFiveAwarded = true;
    state.momentum += 2;
    log("The Senate rallies behind the eastern command: gain 2 Momentum.");
  }
}

function changeStrength(host, amount) {
  state.strength[host] = clamp(state.strength[host] + amount, 0, 6);
}

function totalStrength() { return fronts.reduce((sum, host) => sum + state.strength[host], 0); }
function totalLegions() { return Object.values(state.legions).reduce((sum, count) => sum + count, 0); }
function d6() { return Math.floor(Math.random() * 6) + 1; }

function phaseName() {
  return {crisis: "Receive", command: "Deliberate", orders: "Issue Orders", enemy: "Enemy Design", end: "Complete"}[state.phase] || state.phase;
}

function log(text) {
  const item = document.createElement("li");
  item.innerHTML = text;
  $("#log").prepend(item);
}

function showRules() {
  $("#modalContent").innerHTML = `<div class="modal-inner"><p class="eyebrow">Quick rules</p><h2>How to play</h2>
    <p>Each round reveals a Crisis and its Host order. Choose one Command half, then two different Basic Orders. After your actions, only the named Host Musters or Raids.</p>
    <p><strong>Campaign:</strong> Rome = committed Legions + d6 + support. Enemy = Host Strength + d6. Wins reduce Strength and force retreats.</p>
    <p><strong>Victory:</strong> complete the Scenario objective while Rome, Senate, and Resolve remain above zero. Do not let a Host remain in Aquileia.</p>
    <div class="modal-actions"><button class="primary" id="closeRules">Return</button></div></div>`;
  $("#modal").showModal();
  $("#closeRules").addEventListener("click", () => $("#modal").close());
}

function choose(title, text, options) {
  return new Promise(resolve => {
    $("#modalContent").innerHTML = `<div class="modal-inner"><p class="eyebrow">Decision</p><h2>${title}</h2><p>${text}</p>
      <div class="modal-actions">${options.map(option =>
        `<button class="secondary choice" data-value="${option.value}" ${option.disabled ? "disabled" : ""}>${option.label}</button>`
      ).join("")}</div></div>`;
    $("#modal").showModal();
    $$(".choice").forEach(button => button.addEventListener("click", () => {
      const value = button.dataset.value;
      $("#modal").close();
      resolve(value);
    }));
  });
}

function chooseHost(title, text, excluded = []) {
  return choose(title, text, fronts.map(host => ({
    label: `${HOST_NAMES[host]} — Strength ${state.strength[host]} at ${spaces[state.hosts[host]].name}`,
    value: host, disabled: excluded.includes(host)
  })));
}

function chooseSpace(title, text, allowed) {
  return choose(title, text, allowed.map(id => ({label: spaces[id].name, value: id})));
}

function notice(title, text) {
  return new Promise(resolve => {
    $("#modalContent").innerHTML = `<div class="modal-inner"><p class="eyebrow">Notice</p><h2>${title}</h2><p>${text}</p>
      <div class="modal-actions"><button class="primary" id="noticeClose">Continue</button></div></div>`;
    $("#modal").showModal();
    $("#noticeClose").addEventListener("click", () => { $("#modal").close(); resolve(); });
  });
}

function showDice(title, roman, enemy, text) {
  return new Promise(resolve => {
    $("#modalContent").innerHTML = `<div class="modal-inner"><p class="eyebrow">Battle result</p><h2>${title}</h2>
      <div class="dice"><div><span>Roman</span><div class="die">${roman}</div></div>
      <div><span>Enemy</span><div class="die">${enemy}</div></div></div><p>${text}</p>
      <div class="modal-actions"><button class="primary" id="diceClose">Resolve result</button></div></div>`;
    $("#modal").showModal();
    $("#diceClose").addEventListener("click", () => { $("#modal").close(); resolve(); });
  });
}

init().catch(error => {
  document.body.innerHTML = `<main><section class="panel"><h2>Unable to load the game</h2><p>${error.message}</p></section></main>`;
  console.error(error);
});
