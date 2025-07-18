import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material'
import {
  Search as SearchIcon,
  Description as DocumentIcon,
  Person as PersonIcon,
  LocationOn as LocationIcon,
  Medication as MedicationIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material'
import { useQuery } from 'react-query'
import { apiService } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { SearchResult } from '../types'

const Search: React.FC = () => {
  const [query, setQuery] = useState('')
  const [nResults, setNResults] = useState(10)
  const [minConfidence, setMinConfidence] = useState(0.7)
  const [entityFilter, setEntityFilter] = useState('all')

  const searchQuery = useQuery(
    ['search', query, nResults],
    () => apiService.searchDocuments(query, nResults),
    {
      enabled: query.length > 0,
      staleTime: 30000,
    }
  )

  const handleSearch = () => {
    if (query.trim()) {
      searchQuery.refetch()
    }
  }

  const getEntityIcon = (entityType: string) => {
    switch (entityType.toLowerCase()) {
      case 'person':
        return <PersonIcon />
      case 'location':
        return <LocationIcon />
      case 'medication':
        return <MedicationIcon />
      default:
        return <TrendingIcon />
    }
  }

  const getEntityColor = (entityType: string) => {
    switch (entityType.toLowerCase()) {
      case 'person':
        return 'primary'
      case 'location':
        return 'secondary'
      case 'medication':
        return 'success'
      case 'disease':
        return 'error'
      case 'symptom':
        return 'warning'
      default:
        return 'default'
    }
  }

  const filteredResults = searchQuery.data?.results.filter(result => {
    if (entityFilter === 'all') return true
    
    return result.matched_entities.some(entity => 
      entity.label.toLowerCase() === entityFilter.toLowerCase()
    )
  }) || []

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Search Documents
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Options
              </Typography>

              <TextField
                fullWidth
                label="Search Query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter medical terms, symptoms, medications..."
                multiline
                rows={3}
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Number of Results</InputLabel>
                <Select
                  value={nResults}
                  label="Number of Results"
                  onChange={(e) => setNResults(e.target.value as number)}
                >
                  <MenuItem value={5}>5 results</MenuItem>
                  <MenuItem value={10}>10 results</MenuItem>
                  <MenuItem value={20}>20 results</MenuItem>
                  <MenuItem value={50}>50 results</MenuItem>
                </Select>
              </FormControl>

              <Typography gutterBottom>
                Minimum Confidence: {minConfidence}
              </Typography>
              <Slider
                value={minConfidence}
                onChange={(_, value) => setMinConfidence(value as number)}
                min={0}
                max={1}
                step={0.1}
                marks
                valueLabelDisplay="auto"
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Entity Filter</InputLabel>
                <Select
                  value={entityFilter}
                  label="Entity Filter"
                  onChange={(e) => setEntityFilter(e.target.value)}
                >
                  <MenuItem value="all">All Entities</MenuItem>
                  <MenuItem value="person">Person</MenuItem>
                  <MenuItem value="location">Location</MenuItem>
                  <MenuItem value="medication">Medication</MenuItem>
                  <MenuItem value="disease">Disease</MenuItem>
                  <MenuItem value="symptom">Symptom</MenuItem>
                </Select>
              </FormControl>

              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={!query.trim() || searchQuery.isLoading}
                startIcon={<SearchIcon />}
              >
                {searchQuery.isLoading ? 'Searching...' : 'Search'}
              </Button>

              {searchQuery.isLoading && (
                <LinearProgress sx={{ mt: 2 }} />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Results
                {searchQuery.data && (
                  <Typography component="span" variant="body2" color="textSecondary">
                    {' '}({searchQuery.data.total_results} results in {searchQuery.data.processing_time.toFixed(2)}s)
                  </Typography>
                )}
              </Typography>

              {searchQuery.isError && (
                <Typography color="error">
                  Search failed. Please try again.
                </Typography>
              )}

              {searchQuery.data && filteredResults.length === 0 && (
                <Typography color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
                  No results found for "{query}"
                </Typography>
              )}

              {filteredResults.length > 0 && (
                <List>
                  {filteredResults.map((result, index) => (
                    <React.Fragment key={result.document.id}>
                      <ListItem alignItems="flex-start">
                        <ListItemIcon>
                          <DocumentIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1">
                                {result.document.filename}
                              </Typography>
                              <Chip 
                                label={`${(result.similarity_score * 100).toFixed(1)}% match`}
                                size="small"
                                color="primary"
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="textSecondary" paragraph>
                                Uploaded {formatDistanceToNow(new Date(result.document.uploaded_at), { addSuffix: true })}
                              </Typography>
                              
                              {result.document.extracted_text && (
                                <Typography variant="body2" paragraph>
                                  {result.document.extracted_text.substring(0, 200)}...
                                </Typography>
                              )}

                              {result.matched_entities.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="body2" color="textSecondary" gutterBottom>
                                    Matched Entities:
                                  </Typography>
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                    {result.matched_entities.map((entity, entityIndex) => (
                                      <Chip
                                        key={entityIndex}
                                        icon={getEntityIcon(entity.label)}
                                        label={`${entity.text} (${entity.label})`}
                                        size="small"
                                        color={getEntityColor(entity.label) as any}
                                        variant="outlined"
                                      />
                                    ))}
                                  </Box>
                                </Box>
                              )}

                              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                                <Chip 
                                  label={result.document.status} 
                                  size="small"
                                  color={result.document.status === 'completed' ? 'success' : 
                                         result.document.status === 'processing' ? 'warning' : 'error'}
                                />
                                <Chip 
                                  label={`${result.document.entity_count} entities`}
                                  size="small"
                                  variant="outlined"
                                />
                                {result.document.ocr_confidence && (
                                  <Chip 
                                    label={`OCR: ${(result.document.ocr_confidence * 100).toFixed(1)}%`}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                              </Box>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < filteredResults.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Search 