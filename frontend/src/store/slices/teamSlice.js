import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

const initialState = {
  teams: [],
  currentTeam: null,
  members: [],
  isLoading: false,
  error: null,
};

export const fetchTeams = createAsyncThunk(
  'teams/fetchTeams',
  async () => {
    const response = await api.get('/api/teams/');
    return response.data;
  }
);

export const fetchTeam = createAsyncThunk(
  'teams/fetchTeam',
  async (teamId) => {
    const response = await api.get(`/api/teams/${teamId}/`);
    return response.data;
  }
);

export const createTeam = createAsyncThunk(
  'teams/createTeam',
  async (teamData) => {
    const response = await api.post('/api/teams/', teamData);
    return response.data;
  }
);

export const updateTeam = createAsyncThunk(
  'teams/updateTeam',
  async ({ id, ...teamData }) => {
    const response = await api.put(`/api/teams/${id}/`, teamData);
    return response.data;
  }
);

export const deleteTeam = createAsyncThunk(
  'teams/deleteTeam',
  async (teamId) => {
    await api.delete(`/api/teams/${teamId}/`);
    return teamId;
  }
);

export const fetchTeamMembers = createAsyncThunk(
  'teams/fetchTeamMembers',
  async (teamId) => {
    const response = await api.get(`/api/teams/${teamId}/members/`);
    return response.data;
  }
);

export const addTeamMember = createAsyncThunk(
  'teams/addTeamMember',
  async ({ teamId, userId, role }) => {
    const response = await api.post(`/api/teams/${teamId}/members/`, { user: userId, role });
    return response.data;
  }
);

export const removeTeamMember = createAsyncThunk(
  'teams/removeTeamMember',
  async ({ teamId, memberId }) => {
    await api.delete(`/api/teams/${teamId}/members/${memberId}/`);
    return memberId;
  }
);

const teamSlice = createSlice({
  name: 'teams',
  initialState,
  reducers: {
    clearCurrentTeam: (state) => {
      state.currentTeam = null;
      state.members = [];
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Teams
      .addCase(fetchTeams.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTeams.fulfilled, (state, action) => {
        state.isLoading = false;
        state.teams = Array.isArray(action.payload) ? action.payload : (action.payload?.results || []);
      })
      .addCase(fetchTeams.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch teams';
      })
      // Fetch Team
      .addCase(fetchTeam.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTeam.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentTeam = action.payload;
      })
      .addCase(fetchTeam.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch team';
      })
      // Create Team
      .addCase(createTeam.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createTeam.fulfilled, (state, action) => {
        state.isLoading = false;
        state.teams.push(action.payload);
      })
      .addCase(createTeam.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create team';
      })
      // Update Team
      .addCase(updateTeam.fulfilled, (state, action) => {
        const index = state.teams.findIndex(t => t.id === action.payload.id);
        if (index !== -1) {
          state.teams[index] = action.payload;
        }
        if (state.currentTeam && state.currentTeam.id === action.payload.id) {
          state.currentTeam = action.payload;
        }
      })
      // Delete Team
      .addCase(deleteTeam.fulfilled, (state, action) => {
        state.teams = state.teams.filter(t => t.id !== action.payload);
        if (state.currentTeam && state.currentTeam.id === action.payload) {
          state.currentTeam = null;
          state.members = [];
        }
      })
      // Fetch Team Members
      .addCase(fetchTeamMembers.fulfilled, (state, action) => {
        state.members = action.payload;
      })
      // Add Team Member
      .addCase(addTeamMember.fulfilled, (state, action) => {
        state.members.push(action.payload);
      })
      // Remove Team Member
      .addCase(removeTeamMember.fulfilled, (state, action) => {
        state.members = state.members.filter(m => m.id !== action.payload);
      });
  },
});

export const { clearCurrentTeam, clearError } = teamSlice.actions;
export default teamSlice.reducer;