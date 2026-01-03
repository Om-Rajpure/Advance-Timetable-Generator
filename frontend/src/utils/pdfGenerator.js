import jsPDF from 'jspdf';
import 'jspdf-autotable';

/**
 * Generates a PDF containing timetables for all years and divisions.
 * Each division gets its own page.
 * 
 * @param {Object} fullGrid - The structured grid data { "FE": { "A": { ...days... } } }
 * @param {Object} branchData - Context for headers (Department Name, etc.)
 */
export const generateFullTimetablePDF = (fullGrid, branchData) => {
    const doc = new jsPDF('l', 'mm', 'a4'); // Landscape, millimeters, A4
    const departmentName = branchData?.departmentName || 'Department Timetable';
    const collegeName = branchData?.collegeName || 'College Timetable';

    let isFirstPage = true;

    // Iterate through Years (FE, SE, TE, BE)
    Object.keys(fullGrid).sort().forEach((year) => {
        const divisions = fullGrid[year];

        // Iterate through Divisions (A, B, C...)
        Object.keys(divisions).sort().forEach((div) => {
            if (!isFirstPage) {
                doc.addPage();
            }
            isFirstPage = false;

            const divData = divisions[div];

            // Header
            doc.setFontSize(18);
            doc.text(collegeName, 14, 15);
            doc.setFontSize(14);
            doc.text(`${departmentName} - ${year} Division ${div}`, 14, 22);
            doc.setFontSize(10);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 270, 10, { align: 'right' });

            // Prepare Table Data
            const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const maxSlots = 8; // Assuming 8 slots max for standard view

            // Column Headers
            const head = [['Day', 'Subject', 'Time/Slot', 'Teacher', 'Room']];

            // Transform grid data to table rows
            // For a traditional timetable grid (Time vs Day), we need a matrix.
            // jspdf-autotable works best with rows.
            // Let's create a Grid Layout Table:
            // Columns: Time Slots
            // Rows: Days

            // Determine Slots columns
            const columns = [{ header: 'Day / Time', dataKey: 'day' }];
            for (let i = 1; i <= maxSlots; i++) {
                columns.push({ header: `Slot ${i}`, dataKey: `slot${i}` });
            }

            // Create Rows
            const rows = days.map(day => {
                const row = { day: day };
                const daySlots = divData[day] || {}; // { 1: [], 2: [] }

                for (let i = 1; i <= maxSlots; i++) {
                    const entries = daySlots[i] || [];
                    if (entries.length > 0) {
                        // Format cell content
                        // E.g. "Maths (Prof. X) [Room 1]"
                        const content = entries.map(e => {
                            const room = e.room ? `[${e.room}]` : '';
                            const batch = e.batch ? `(${e.batch})` : '';
                            return `${e.subject}\n${e.teacher} ${room} ${batch}`;
                        }).join('\n---\n');
                        row[`slot${i}`] = content;
                    } else {
                        row[`slot${i}`] = '';
                    }
                }
                return row;
            });

            // Specific Styles for Timetable
            doc.autoTable({
                columns: columns,
                body: rows,
                startY: 30,
                styles: {
                    fontSize: 8,
                    overflow: 'linebreak',
                    cellPadding: 2,
                    valign: 'middle'
                },
                headStyles: {
                    fillColor: [41, 128, 185],
                    textColor: 255,
                    fontSize: 9,
                    halign: 'center'
                },
                columnStyles: {
                    day: { fontStyle: 'bold', width: 25, fillColor: [240, 240, 240] }
                },
                theme: 'grid'
            });

            // Footer
            const pageCount = doc.internal.getNumberOfPages();
            doc.setFontSize(8);
            doc.text(`Page ${pageCount}`, 14, 200);
        });
    });

    doc.save('Complete_Timetable.pdf');
};
