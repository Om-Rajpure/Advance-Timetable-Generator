import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

import { generateDayLayout } from './timetableTransforms';

/**
 * Generates a PDF containing timetables for all years and divisions.
 * Each division gets its own page.
 * 
 * @param {Object} fullGrid - The structured grid data { "FE": { "A": { ...days... } } }
 * @param {Object} branchData - Context for headers (Department Name, etc.)
 */
export const generateFullTimetablePDF = (fullGrid, branchData, customLayout = null) => {
    try {
        console.log("📄 PDF Generation Started");

        if (!fullGrid || Object.keys(fullGrid).length === 0) {
            alert("❌ No timetable data to download! (Grid is empty)");
            return;
        }

        // Initialize jsPDF
        const doc = new jsPDF('l', 'mm', 'a4');

        const departmentName = branchData?.departmentName || 'Department Timetable';
        const collegeName = branchData?.collegeName || 'College Timetable';

        let isFirstPage = true;
        let hasContent = false;

        // Iterate through Years (FE, SE, TE, BE)
        Object.keys(fullGrid).sort().forEach((year) => {
            const divisions = fullGrid[year];

            // Iterate through Divisions (A, B, C...)
            Object.keys(divisions).sort().forEach((div) => {
                if (!isFirstPage) {
                    doc.addPage();
                }
                isFirstPage = false;
                hasContent = true;

                const divData = divisions[div];

                // Header
                doc.setFontSize(18);
                doc.text(collegeName || "College Timetable", 14, 15);
                doc.setFontSize(14);
                doc.text(`${departmentName} - ${year} Division ${div}`, 14, 22);
                doc.setFontSize(10);
                doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 270, 10, { align: 'right' });

                // Prepare Table Data
                const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

                // Dynamic Layout Generation
                const layout = customLayout || generateDayLayout(branchData);
                const columns = [{ header: 'Day', dataKey: 'day' }];

                layout.forEach((col, i) => {
                    if (col.type === 'lecture') {
                        columns.push({ header: col.label, dataKey: `slot${col.index}` });
                    } else if (col.type === 'recess') {
                        columns.push({ header: col.label, dataKey: `recess_${i}` });
                    }
                });

                // Create Rows
                const rows = days.map(day => {
                    const row = { day: day };
                    const daySlots = divData[day] || {};

                    layout.forEach((col, i) => {
                        if (col.type === 'lecture') {
                            const entries = daySlots[col.index] || [];
                            const key = `slot${col.index}`;

                            if (entries.length > 0) {
                                const content = entries.map(e => {
                                    const room = e.room ? `[${e.room}]` : '';
                                    const batch = e.batch ? `(${e.batch})` : '';
                                    // Only show teacher if present
                                    const teacher = e.teacher && e.teacher !== 'Unknown' ? e.teacher : '';
                                    return `${e.subject} ${batch}\n${teacher} ${room}`;
                                }).join('\n---\n');
                                row[key] = content;
                            } else {
                                row[key] = '';
                            }
                        } else if (col.type === 'recess') {
                            row[`recess_${i}`] = 'BREAK';
                        }
                    });

                    return row;
                });

                // Render Table explicit call
                autoTable(doc, {
                    columns: columns,
                    body: rows,
                    startY: 30,
                    styles: {
                        fontSize: 7, // Smaller font for fitting
                        overflow: 'linebreak',
                        cellPadding: 1,
                        valign: 'middle',
                        halign: 'center',
                        lineWidth: 0.1,
                    },
                    headStyles: {
                        fillColor: [41, 128, 185],
                        textColor: 255,
                        fontSize: 8,
                        halign: 'center',
                        fontStyle: 'bold'
                    },
                    columnStyles: {
                        day: { fontStyle: 'bold', width: 22, fillColor: [245, 245, 245], halign: 'left' }
                    },
                    theme: 'grid'
                });

                // Page Footer
                const pageCount = doc.internal.getNumberOfPages();
                doc.setFontSize(8);
                doc.text(`Page ${pageCount}`, 14, 200);
            });
        });

        if (!hasContent) {
            alert("❌ No classes found to generate PDF.");
            return;
        }

        console.log("💾 Saving PDF...");
        doc.save('Complete_College_Timetable.pdf');

    } catch (error) {
        console.error("PDF Generation Error:", error);
        alert(`❌ Failed to generate PDF: ${error.message}`);
    }
};
