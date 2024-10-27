const sections = [
    "h2.layout.Section",
    "h3.layout.Subsection",
    "h4.layout.Subsubsection",
    "h5.layout.Paragraph",
    "h6.Subparagraph"
]

const counters = [0, 0, 0, 0, 0];  // Supports from <h2> up to <h6>

document.addEventListener("DOMContentLoaded", function() {
    // Fetch depth limit from the class of an element inside <head> with the class "secnumdepth"
    const depthElement = document.querySelector("head .secnumdepth");
    const maxDepth = depthElement ? parseInt([...depthElement.classList].find(cls => !isNaN(cls))) : 6; // Default to 6 if not found

    const headers = document.querySelectorAll(sections.join(", "));
    headers.forEach(header => {
        const level = parseInt(header.tagName[1]) - 2;

        if (level < maxDepth) {
            // Update counters up to the allowed depth
            counters[level]++;
            for (let i = level + 1; i < counters.length; i++) {
                counters[i] = 0;
            }

            // Generate numbering prefix within the allowed depth
            const sectionNumber = counters.slice(0, level + 1).join(".");
            header.innerHTML = `${sectionNumber} ${header.innerHTML}`;
            header.parentElement.setAttribute("data-index", sectionNumber);
        }
    })

    const parts = document.querySelectorAll("div.layout.Part");
    let part_counter = 0
    parts.forEach(p => {
        if (-2 < maxDepth) {
            // Update counters up to the allowed depth
            part_counter++;
    
            // Generate numbering prefix within the allowed depth
            p.innerHTML = `Part ${toRoman(part_counter)}<br />${p.innerHTML}`;
            p.parentElement.setAttribute("data-index", part_counter);
    }})

    const chapters = document.querySelectorAll("div.layout.Chapter");
    let chapter_counter = 0
    chapters.forEach(c => {
        if (-1 < maxDepth) {
            // Update counters up to the allowed depth
            part_counter++;
    
            // Generate numbering prefix within the allowed depth
            c.innerHTML = `Chapter ${chapter_counter} ${c.innerHTML}`;
            c.parentElement.setAttribute("data-index", chapter_counter);
    }})
});


function toRoman(num) {
    const romanNumerals = [
        { value: 1000, symbol: "M" },
        { value: 900, symbol: "CM" },
        { value: 500, symbol: "D" },
        { value: 400, symbol: "CD" },
        { value: 100, symbol: "C" },
        { value: 90, symbol: "XC" },
        { value: 50, symbol: "L" },
        { value: 40, symbol: "XL" },
        { value: 10, symbol: "X" },
        { value: 9, symbol: "IX" },
        { value: 5, symbol: "V" },
        { value: 4, symbol: "IV" },
        { value: 1, symbol: "I" }
    ];
    
    let result = "";

    // Loop through each Roman numeral value
    romanNumerals.forEach(({ value, symbol }) => {
        while (num >= value) {
            result += symbol;
            num -= value;
        }
    });

    return result;
}
