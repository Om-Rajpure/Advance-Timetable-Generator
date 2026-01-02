const DEBUG_DATA = {
    "SE-A": {
        "Monday": [
            { id: "d1", slot: 1, subject: "DEBUG-THEORY", type: "THEORY", teacher: "TESTER", room: "101" },
            { id: "d2", slot: 2, subject: "DEBUG-LAB", type: "LAB", teacher: "TESTER", room: "LAB-A", batch: "B1" }
        ],
        "Tuesday": [
            { id: "d3", slot: 1, subject: "DEBUG-SUB", type: "THEORY", teacher: "TESTER", room: "101" }
        ]
    },
    "SE-B": {
        "Monday": [{ id: "d4", slot: 1, subject: "DEBUG-B", type: "THEORY", teacher: "TESTER", room: "102" }]
    }
};

const transformToGrid = (data, branchData) => {
    if (!data) return {};

    const grid = {};

    console.log("transformToGrid Input keys:", Object.keys(data));

    Object.keys(data).forEach(key => {
        // Check if key is "Year-Div" e.g. "SE-A"
        if (key.includes('-')) {
            const parts = key.split('-');
            const div = parts.pop();
            const year = parts.join('-');

            console.log(`parsing: ${key} -> Y:${year} D:${div}`);

            if (!grid[year]) grid[year] = {};
            if (!grid[year][div]) grid[year][div] = {};

            const schedule = data[key]; // { Day: [Slots] }

            if (Array.isArray(schedule)) {
                console.log("Schedule is ARRAY (Not expected for DEBUG_DATA)");
            } else {
                Object.keys(schedule).forEach(day => {
                    console.log(`  Processing Day: ${day}`);
                    if (!grid[year][div][day]) grid[year][div][day] = {};

                    const slotsList = schedule[day];
                    if (Array.isArray(slotsList)) {
                        console.log(`    Slots Array found with ${slotsList.length} items`);
                        slotsList.forEach(slot => {
                            const slotIdx = slot.slot;
                            if (!grid[year][div][day][slotIdx]) grid[year][div][day][slotIdx] = [];
                            grid[year][div][day][slotIdx].push(slot);
                            console.log(`      -> Pushed to Slot ${slotIdx}`);
                        });
                    } else {
                        console.log("    Slots List is NOT array:", typeof slotsList);
                    }
                });
            }
        } else {
            console.log("Key does not contain '-':", key);
        }
    });

    return grid;
};

// 1. RUN TRANSFORM
console.log("--- RUNNING TRANSFORM ---");
const transformed = transformToGrid(DEBUG_DATA, {});
console.log("\n--- TRANSFORM OUTPUT ---");
console.log(JSON.stringify(transformed, null, 2));


// 2. SIMULATE TIMETABLE PAGE
const selectedYear = "SE";
const selectedDivision = "A";

console.log(`\n--- SIMULATING TIMETABLE PAGE (${selectedYear}, ${selectedDivision}) ---`);
const currentGrid = (transformed[selectedYear] && transformed[selectedYear][selectedDivision])
    ? transformed[selectedYear][selectedDivision]
    : {};
console.log("Current Grid Keys:", Object.keys(currentGrid));
console.log("Current Grid Content:", JSON.stringify(currentGrid, null, 2));


// 3. SIMULATE TIMETABLE GRID RENDERING
console.log("\n--- SIMULATING GRID RENDER ---");
const days = ['Monday', 'Tuesday'];
days.forEach(day => {
    // Try Slot 1
    const cellSlots = currentGrid[day]?.[1] || [];
    console.log(`Day: ${day}, Slot 1:`, cellSlots.length > 0 ? "FOUND" : "EMPTY");
    if (cellSlots.length > 0) console.log(JSON.stringify(cellSlots[0]));
});
