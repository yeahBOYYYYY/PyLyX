document.addEventListener("DOMContentLoaded", function() {
    function isScript(name) {
        // Select all <script> elements in the document
        const scripts = document.querySelectorAll('script');
        
        // Loop through each <script> and check if its src ends with the given string
        for (let script of scripts) {
            if (script.src.endsWith(name)) {
                return true; // Found a matching script element
            }
        }
        return false
    }
    
    function createPrefix(current, last, last_index, counter) {
        if (isScript("theorems-sec.js")) {
            let element = current
            while (element !== null && element.className != `layout ${"Section"}`) {
                    element = element.parentElement;
            }
            if (element !== null && element !== last) {
                last = element
                if (last !== null && last.getAttribute("id") !== null) {
                    last_index = parseInt(last.getAttribute("id").replace(/\D/g, ""))
                }
                counter = 0
            }
            counter++;
            return [`${last_index}.${counter}`, last, last_index, counter]
        } else {
            counter++;
            return [counter, last, last_index, counter]
        }
    }
    
    const names = {
        "Theorem": "b",
        "Corollary": "b",
        "Lemma": "i",
        "Proposition": "b",
        "Conjecture": "b",
        "Definition": "b",
        "Example": "b",
        "Problem": "b",
        "Exercise": "b",
        "Solution": "b",
        "Remark": "",
        "Claim": "b",
        "Fact": "b"
    }

    const selectors = [
        "div.layout.Theorem",
        "div.layout.Corollary",
        "div.layout.Lemma",
        "div.layout.Proposition",
        "div.layout.Conjecture",
        "div.layout.Definition",
        "div.layout.Example",
        "div.layout.Problem",
        "div.layout.Exercise",
        "div.layout.Solution",
        "div.layout.Remark",
        "div.layout.Claim",
        "div.layout.Fact"
    ]

    let last = null
    let last_index = 0
    let counter = 0
    let prefix = ""
    const theorems = document.querySelectorAll(selectors.join(", "))
    theorems.keys().forEach(t => {
        [prefix, last, last_index, counter] = createPrefix(t, last, last_index, counter)
        t.id = `${t.classList.item(1)}_${prefix}`

        let start = ""
        let end = ""
        let key = t.className.split(" ").at(-1)
        if (Boolean(names.key)) {
            start += `<${names.key}>`
            end += `</${names.key}>`
        }
        if (t.querySelector("span.inset.Argument") == null) {
            end += "."
        }
        t.innerHTML = `${start}${key} ${prefix}${end} ${t.innerHTML}`;
    })

    names.forEach(key => {
        const theorems = document.querySelectorAll(`div.layout.${key}_`)
        theorems.forEach(t => {
            let text = ""
            if (names.key) {
                text += `<${names.key}>${key}</${names.key}>`
            } else {
                text += `${key}`
            }
            if (t.querySelectorAll("span.inset.Argument") == null) {
                text += "."
            }
            t.innerHTML = `${text} ${t.innerHTML}`
        })
    })

    const cases = document.querySelectorAll("div.layout.Case")
    let index = 0
    cases.forEach(c => {
        if (c.previousElementSibling.className !== "layout Case") {
            index = 0
        }
        index += 1
        c.innerHTML = `<i>Case ${index}</i>. ${c.innerHTML}`;
    })

    const proofs = document.querySelectorAll("div.layout.Proof")
    proofs.forEach(p => {
        p.innerHTML = `<i>Proof</i>. ${p.innerHTML}<span style="font-size: 150%; position: absolute; left: 100%;">■</span>`;
    })


    const links = document.querySelectorAll("a.inset.CommandInset.ref")
    links.forEach (l => {
        let id = l.getAttribute("href").slice(1)
        let parent = document.getElementById(id).parentElement
        if (parent.querySelector("span.inset.Argument") != null) {
            l.innerHTML = parent.querySelector("span.inset.Argument").innerHTML
        } else {
            l.innerHTML = parent.getAttribute("id").replace(/[^0-9.]/g, "")
        }
    })
});
