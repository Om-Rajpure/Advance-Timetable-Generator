/**
 * PDF Parser Client Utility
 * Handles PDF file uploads and communication with backend PDF parser
 */

const API_BASE_URL = 'http://localhost:5000/api'

/**
 * Upload PDF file to backend for extraction
 */
export async function uploadPdfFile(file) {
    try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${API_BASE_URL}/upload/timetable/pdf`, {
            method: 'POST',
            body: formData
        })

        const result = await response.json()

        if (!response.ok) {
            throw new Error(result.error || 'Failed to upload PDF')
        }

        return handlePdfResponse(result)
    } catch (error) {
        throw new Error(`PDF upload failed: ${error.message}`)
    }
}

/**
 * Handle and normalize PDF extraction response from backend
 */
export function handlePdfResponse(response) {
    if (!response.success) {
        throw new Error(response.error || 'PDF extraction failed')
    }

    return {
        success: true,
        pdfInfo: {
            type: response.type,
            pages: response.pages,
            extractionMethod: response.extractionMethod,
            rowCount: response.rowCount
        },
        data: response.data,
        meta: {
            fields: response.data.length > 0 ? Object.keys(response.data[0]) : []
        }
    }
}

export default {
    uploadPdfFile,
    handlePdfResponse
}
