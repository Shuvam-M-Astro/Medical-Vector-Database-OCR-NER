import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Button,
} from '@mui/material'

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Settings
              </Typography>
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable real-time processing"
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Auto-refresh dashboard"
              />
              
              <FormControlLabel
                control={<Switch />}
                label="Enable notifications"
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Show processing progress"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                API Configuration
              </Typography>
              
              <TextField
                fullWidth
                label="API Base URL"
                defaultValue="http://localhost:8000"
                margin="normal"
              />
              
              <TextField
                fullWidth
                label="Request Timeout (seconds)"
                defaultValue="30"
                margin="normal"
                type="number"
              />
              
              <TextField
                fullWidth
                label="Max File Size (MB)"
                defaultValue="50"
                margin="normal"
                type="number"
              />
              
              <Button variant="contained" sx={{ mt: 2 }}>
                Save Settings
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Settings 