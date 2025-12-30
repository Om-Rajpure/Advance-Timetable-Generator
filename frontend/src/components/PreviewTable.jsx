import React from 'react'

function PreviewTable({ data = [], columns = [], title = '', onEdit, validationResults = {}, isEditable = false, onDataUpdate }) {
    const [sortColumn, setSortColumn] = React.useState(null)
    const [sortDirection, setSortDirection] = React.useState('asc')

    if (data.length === 0) {
        return (
            <div className="preview-table-empty">
                <div className="empty-icon">📋</div>
                <p>No data to preview yet</p>
            </div>
        )
    }

    const handleSort = (columnKey) => {
        if (sortColumn === columnKey) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
        } else {
            setSortColumn(columnKey)
            setSortDirection('asc')
        }
    }

    const sortedData = [...data].sort((a, b) => {
        if (!sortColumn) return 0

        const aVal = a[sortColumn]
        const bVal = b[sortColumn]

        if (typeof aVal === 'string') {
            return sortDirection === 'asc'
                ? aVal.localeCompare(bVal)
                : bVal.localeCompare(aVal)
        }

        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })

    const getRowStatus = (row) => {
        // Check if this row has any validation issues
        const rowErrors = validationResults.errors?.filter(err =>
            err.value === row.name || err.index === row.index
        ) || []

        const rowWarnings = validationResults.warnings?.filter(warn =>
            warn.value === row.name || warn.index === row.index
        ) || []

        if (rowErrors.length > 0) return 'error'
        if (rowWarnings.length > 0) return 'warning'
        return 'valid'
    }

    return (
        <div className="preview-table-container">
            {title && (
                <div className="preview-table-header">
                    <h3 className="preview-table-title">{title}</h3>
                    <div className="preview-table-count">{data.length} item{data.length !== 1 ? 's' : ''}</div>
                </div>
            )}

            <div className="preview-table-wrapper">
                <table className="preview-table">
                    <thead>
                        <tr>
                            {columns.map(col => (
                                <th
                                    key={col.key}
                                    className={`preview-table-th ${col.sortable !== false ? 'sortable' : ''}`}
                                    onClick={() => col.sortable !== false && handleSort(col.key)}
                                >
                                    <div className="th-content">
                                        <span>{col.label}</span>
                                        {col.sortable !== false && sortColumn === col.key && (
                                            <span className="sort-indicator">
                                                {sortDirection === 'asc' ? '▲' : '▼'}
                                            </span>
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sortedData.map((row, rowIndex) => {
                            const rowStatus = getRowStatus(row)
                            return (
                                <tr
                                    key={row.id || rowIndex}
                                    className={`preview-table-row ${rowStatus}`}
                                >
                                    {columns.map(col => {
                                        const isCellEditable = isEditable && col.editable

                                        return (
                                            <td key={col.key} className={`preview-table-td ${isCellEditable ? 'editable-cell' : ''}`}>
                                                {isCellEditable ? (
                                                    col.type === 'select' ? (
                                                        <select
                                                            value={row[col.key]}
                                                            onChange={(e) => {
                                                                const val = e.target.value === 'true' ? true : e.target.value === 'false' ? false : e.target.value
                                                                const updatedRow = { ...row, [col.key]: val }
                                                                // Call update handler
                                                                const newData = [...data]
                                                                const index = newData.findIndex(item => item.id === row.id)
                                                                if (index !== -1) {
                                                                    newData[index] = updatedRow
                                                                    onDataUpdate && onDataUpdate(newData)
                                                                }
                                                            }}
                                                        >
                                                            {col.options.map(opt => (
                                                                <option key={opt.value} value={opt.value}>
                                                                    {opt.label}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    ) : (
                                                        <input
                                                            type={col.type || 'text'}
                                                            value={row[col.key]}
                                                            onChange={(e) => {
                                                                const val = col.type === 'number' ? parseInt(e.target.value) : e.target.value
                                                                const updatedRow = { ...row, [col.key]: val }
                                                                // Call update handler
                                                                const newData = [...data]
                                                                const index = newData.findIndex(item => item.id === row.id)
                                                                if (index !== -1) {
                                                                    newData[index] = updatedRow
                                                                    onDataUpdate && onDataUpdate(newData)
                                                                }
                                                            }}
                                                        />
                                                    )
                                                ) : (
                                                    col.render ? col.render(row[col.key], row) : row[col.key]
                                                )}
                                            </td>
                                        )
                                    })}
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>

            <div className="preview-table-legend">
                <div className="legend-item">
                    <span className="legend-badge valid">✓</span>
                    <span>Valid</span>
                </div>
                <div className="legend-item">
                    <span className="legend-badge warning">⚠</span>
                    <span>Warning</span>
                </div>
                <div className="legend-item">
                    <span className="legend-badge error">✗</span>
                    <span>Error</span>
                </div>
            </div>
        </div>
    )
}

export default PreviewTable
