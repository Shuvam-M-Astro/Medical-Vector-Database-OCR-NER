import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { DataGrid, GridColDef, GridValueGetterParams } from '@mui/x-data-grid'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiService } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'

const Documents: React.FC = () => {
  const [selectedDocument, setSelectedDocument] = useState<any>(null)
  const [viewDialogOpen, setViewDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: documents, isLoading } = useQuery('documents', () => 
    apiService.getDocuments(1000, 0)
  )

  const deleteMutation = useMutation(
    (documentId: string) => apiService.deleteDocument(documentId),
    {
      onSuccess: () => {
        toast.success('Document deleted successfully')
        queryClient.invalidateQueries('documents')
        queryClient.invalidateQueries('stats')
      },
      onError: (error: any) => {
        toast.error(`Delete failed: ${error.response?.data?.detail || error.message}`)
      },
    }
  )

  const handleDelete = (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(documentId)
    }
  }

  const handleView = (document: any) => {
    setSelectedDocument(document)
    setViewDialogOpen(true)
  }

  const columns: GridColDef[] = [
    {
      field: 'filename',
      headerName: 'Filename',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={
            params.value === 'completed' ? 'success' :
            params.value === 'processing' ? 'warning' : 'error'
          }
        />
      ),
    },
    {
      field: 'entity_count',
      headerName: 'Entities',
      width: 100,
      type: 'number',
    },
    {
      field: 'uploaded_at',
      headerName: 'Uploaded',
      width: 150,
      valueGetter: (params: GridValueGetterParams) =>
        formatDistanceToNow(new Date(params.value), { addSuffix: true }),
    },
    {
      field: 'file_size',
      headerName: 'Size',
      width: 100,
      valueGetter: (params: GridValueGetterParams) =>
        `${(params.value / 1024 / 1024).toFixed(1)} MB`,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleView(params.row)}
            title="View details"
          >
            <ViewIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row.id)}
            title="Delete document"
            color="error"
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ),
    },
  ]

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Documents ({documents?.length || 0})
        </Typography>
        <Button variant="contained" color="primary">
          Export Data
        </Button>
      </Box>

      <Card>
        <CardContent>
          <DataGrid
            rows={documents || []}
            columns={columns}
            loading={isLoading}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{
              pagination: {
                paginationModel: { page: 0, pageSize: 25 },
              },
            }}
            autoHeight
            disableRowSelectionOnClick
          />
        </CardContent>
      </Card>

      {/* Document Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Document Details: {selectedDocument?.filename}
        </DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Basic Information
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Filename:</strong> {selectedDocument.filename}
                </Typography>
                <Typography variant="body2">
                  <strong>Status:</strong> {selectedDocument.status}
                </Typography>
                <Typography variant="body2">
                  <strong>File Size:</strong> {(selectedDocument.file_size / 1024 / 1024).toFixed(2)} MB
                </Typography>
                <Typography variant="body2">
                  <strong>Uploaded:</strong> {formatDistanceToNow(new Date(selectedDocument.uploaded_at), { addSuffix: true })}
                </Typography>
                <Typography variant="body2">
                  <strong>Entities Found:</strong> {selectedDocument.entity_count}
                </Typography>
                {selectedDocument.ocr_confidence && (
                  <Typography variant="body2">
                    <strong>OCR Confidence:</strong> {(selectedDocument.ocr_confidence * 100).toFixed(1)}%
                  </Typography>
                )}
              </Box>

              {selectedDocument.extracted_text && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Extracted Text
                  </Typography>
                  <Box sx={{ 
                    maxHeight: 200, 
                    overflow: 'auto', 
                    p: 2, 
                    bgcolor: 'grey.50', 
                    borderRadius: 1,
                    mb: 2 
                  }}>
                    <Typography variant="body2">
                      {selectedDocument.extracted_text}
                    </Typography>
                  </Box>
                </>
              )}

              {selectedDocument.entities && selectedDocument.entities.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Extracted Entities
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedDocument.entities.map((entity: any, index: number) => (
                      <Chip
                        key={index}
                        label={`${entity.text} (${entity.label})`}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Documents 