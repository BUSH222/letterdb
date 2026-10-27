// Tag inputs for keywords and regions on the new/edit letter pages (markup: templates/_letter_fields.html).
// Typing 3+ letters lists matching existing tags from /search_keyword_region; clicking one adds it to the list.
// Enter adds the highlighted result, or else the typed text as a new tag, and never submits the form.
// Tags only live in the page (as hidden inputs) until the form is saved.
(function () {
    "use strict";

    var MIN_LETTERS = 3;

    function fold(s) {
        return s.trim().replace(/\s+/g, " ").toLowerCase().replace(/ё/g, "е");
    }

    function setup(root) {
        var kind = root.dataset.kind;
        var input = root.querySelector("input[type=text]");
        var results = root.querySelector(".tag-results");
        var tagList = root.querySelector(".tag-list");
        var template = root.querySelector("template");
        var names = [];
        var active = -1;
        var timer = null;
        var request = null;

        function hasTag(value) {
            var key = fold(value);
            return Array.from(tagList.querySelectorAll("input[type=hidden]")).some(function (el) {
                return fold(el.value) === key;
            });
        }

        function addTag(value) {
            value = value.trim().replace(/\s+/g, " ");
            if (value && !hasTag(value)) {
                var item = template.content.firstElementChild.cloneNode(true);
                item.querySelector(".tag-text").textContent = value;
                item.querySelector("input[type=hidden]").value = value;
                tagList.appendChild(item);
            }
            input.value = "";
            hide();
            input.focus();
        }

        function hide() {
            names = [];
            active = -1;
            results.classList.remove("show");
            results.replaceChildren();
            input.setAttribute("aria-expanded", "false");
            input.removeAttribute("aria-activedescendant");
        }

        function render() {
            results.replaceChildren();
            names.forEach(function (name, i) {
                var option = document.createElement("button");
                option.type = "button";
                option.id = root.dataset.name + "-result-" + i;
                option.className = "dropdown-item" + (i === active ? " active" : "");
                option.setAttribute("role", "option");
                option.setAttribute("aria-selected", i === active ? "true" : "false");
                option.textContent = name;
                // mousedown rather than click, so the input keeps focus
                option.addEventListener("mousedown", function (e) {
                    e.preventDefault();
                    addTag(name);
                });
                results.appendChild(option);
            });
            var open = names.length > 0;
            results.classList.toggle("show", open);
            input.setAttribute("aria-expanded", open ? "true" : "false");
            if (active >= 0) {
                input.setAttribute("aria-activedescendant", results.children[active].id);
                results.children[active].scrollIntoView({ block: "nearest" });
            } else {
                input.removeAttribute("aria-activedescendant");
            }
        }

        function search() {
            var query = input.value.trim();
            if (request) request.abort();
            if (query.length < MIN_LETTERS) {
                hide();
                return;
            }
            request = new AbortController();
            fetch("/search_keyword_region?" + new URLSearchParams([[kind, query]]), { signal: request.signal })
                .then(function (response) { return response.ok ? response.json() : []; })
                .then(function (found) {
                    names = found.filter(function (name) { return !hasTag(name); });
                    active = -1;
                    render();
                })
                .catch(function (err) {
                    if (err.name !== "AbortError") hide();
                });
        }

        input.addEventListener("input", function () {
            clearTimeout(timer);
            timer = setTimeout(search, 150);
        });

        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault(); // never submit the form from here
                if (active >= 0) {
                    addTag(names[active]);
                } else {
                    // An exact match (ignoring case and ё/е) uses the existing spelling.
                    var typed = fold(input.value);
                    var match = names.find(function (name) { return fold(name) === typed; });
                    addTag(match || input.value);
                }
            } else if (e.key === "ArrowDown" && names.length) {
                e.preventDefault();
                active = (active + 1) % names.length;
                render();
            } else if (e.key === "ArrowUp" && names.length) {
                e.preventDefault();
                active = active <= 0 ? names.length - 1 : active - 1;
                render();
            } else if (e.key === "Escape" && names.length) {
                e.preventDefault();
                hide();
            }
        });

        input.addEventListener("blur", hide);

        tagList.addEventListener("click", function (e) {
            var remove = e.target.closest(".tag-remove");
            if (remove) remove.closest("li").remove();
        });
    }

    document.querySelectorAll(".tag-input").forEach(setup);
})();
