document.addEventListener("DOMContentLoaded", function() {
    const sections = ["div.layout.Part", "div.layout.Chapter", "h2.layout.Section", "h3.layout.Subsection", "h4.layout.Subsubsection", "h5.layout.Paragraph", "h6.Subparagraph"]
    const counters = [0, 0, 0, 0, 0, 0, 0];

    // Retrieve section depth from an element in <head>
    const depthElement = document.querySelector("head .secnumdepth");
    const sectionMaxDepth = depthElement ? parseInt([...depthElement.classList].find(cls => !isNaN(cls))) : 6; // Default to 6 if not found
    // Retrieve TOC depth from another element or set directly as a constant
    const tocDepthElement = document.querySelector("head .tocdepth");
    const tocMaxDepth = tocDepthElement ? parseInt([...tocDepthElement.classList].find(cls => !isNaN(cls))) : 7; // Default to 6 if not found

    const maxDepth = Math.max(sectionMaxDepth, tocMaxDepth)

    // Function to convert number to Roman numerals
    function toRoman(num) {
        const romanNumerals = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"];
        const values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
        let roman = "";
        for (let i = 0; i < values.length; i++) {
            while (num >= values[i]) {
                roman += romanNumerals[i];
                num -= values[i];
            }
        }
        return roman;
    }

    function create (tocContainer, level=0, roman=false) {
        const tocList = document.createElement("ul");
        const elements = document.querySelectorAll(sections[level]);
        elements.forEach(element => {
            if (level < maxDepth) {
                // Update counters up to the allowed depth
                counters[level]++;
                if (level > 1) {
                    for (let i = level + 1; i < counters.length; i++) {
                        counters[i] = 0;
                    }
                }
                let counter = counters[level]
                element.parentElement.id = `${element.classList.item(1)}_${counter}`;
        
                // Generate numbering prefix within the allowed depth
                if (level-2 < sectionMaxDepth) {
                    if (roman) {
                        element.innerHTML = `${element.classList.item(1)} ${toRoman(counter)}<br />${element.innerHTML}`;
                    } else {
                        element.innerHTML = element.parentElement.id.replace("_", " ");
                    }
                }
                let tocItem = tocContainer
                if (level-2 < tocMaxDepth) {
                    tocItem = document.createElement("li");
                    let link = document.createElement("a");
                    link.href = `#${element.parentElement.id}`;
                    link.textContent = element.parentElement.id.replace("_", " ");
                    tocItem.appendChild(link);
                    tocList.appendChild(tocItem)
                    tocContainer.appendChild(tocList)
                }
                level = level+1
                create(tocItem, level)
            }
        })
    }

    tocs = document.querySelectorAll(".inset.CommandInset.toc")
    tocs.forEach(toc => {
        toc.innerHTML = "<h2>Table of Contents</h2>" + toc.innerHTML;
        create(toc, 0, true)
    })
});
