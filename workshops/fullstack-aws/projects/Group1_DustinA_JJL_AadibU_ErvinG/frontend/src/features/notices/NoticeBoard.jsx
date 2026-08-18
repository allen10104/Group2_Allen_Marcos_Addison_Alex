import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, Typography, Box, Chip, CircularProgress, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem } from "@mui/material";
import { useForm } from "react-hook-form";
import api from "../../api/axios";
import CreateNoticeForm from "./CreateNoticeForm";

// 1. Updated Edit Modal to restrict department choices
function EditNoticeDialog({ notice, currentUser, onClose }) {
  const queryClient = useQueryClient();
  
  const { register, handleSubmit } = useForm({
    defaultValues: {
      title: notice.title,
      content: notice.content,
      department: notice.department,
    }
  });

  const mutation = useMutation({
    mutationFn: async (updatedData) => await api.put(`/notices/${notice.id}`, updatedData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notices"] });
      onClose();
    },
  });

  return (
    <Dialog open={true} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Edit Notice</DialogTitle>
      <Box component="form" onSubmit={handleSubmit((data) => mutation.mutate(data))}>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Title" size="small" {...register("title", { required: true })} />
          <TextField label="Message" multiline rows={4} {...register("content", { required: true })} />
          <TextField select label="Department" size="small" defaultValue={notice.department} {...register("department")}>
            <MenuItem value="all_employees">All Employees</MenuItem>
            {currentUser.department !== "all_employees" && (
              <MenuItem value={currentUser.department}>
                {currentUser.department.replace('_', ' ').toUpperCase()}
              </MenuItem>
            )}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={mutation.isPending}>Save</Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}

// 2. Updated Main Component with Filtering
export default function NoticeBoard({ logout }) {
  const queryClient = useQueryClient();
  const [editingNotice, setEditingNotice] = useState(null);
  
  // New state to track the active filter
  const [activeFilter, setActiveFilter] = useState("all"); 

  const { data: currentUser } = useQuery({
    queryKey: ["users", "me"],
    queryFn: async () => (await api.get("/users/me")).data,
  });

  const { data: notices, isLoading, isError } = useQuery({
    queryKey: ["notices", "feed"],
    queryFn: async () => (await api.get("/notices/feed")).data,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => await api.delete(`/notices/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notices"] }),
  });

  // Apply the filter to the notices array before rendering
  const filteredNotices = notices?.filter(notice => {
    if (activeFilter === "all") return true;
    return notice.department === activeFilter;
  });

  return (
    <Box sx={{ p: 4, maxWidth: 800, margin: '0 auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h3">Noticeboard</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {currentUser && <Typography variant="subtitle1">Welcome, {currentUser.username}</Typography>}
          <Button variant="outlined" color="error" onClick={logout}>Logout</Button>
        </Box>
      </Box>

      {/* Pass currentUser down so the form knows what to restrict */}
      <CreateNoticeForm currentUser={currentUser} />

      <Box sx={{ mt: 6, mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h5">Recent Notices</Typography>
        
        {/* The Filter UI */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip 
            label="All Feed" 
            color={activeFilter === "all" ? "primary" : "default"} 
            onClick={() => setActiveFilter("all")} 
            clickable 
          />
          <Chip 
            label="All Employees Tag" 
            color={activeFilter === "all_employees" ? "primary" : "default"} 
            onClick={() => setActiveFilter("all_employees")} 
            clickable 
          />
          {currentUser && currentUser.department !== "all_employees" && (
            <Chip 
              label={`${currentUser.department.replace('_', ' ').toUpperCase()} Tag`} 
              color={activeFilter === currentUser.department ? "primary" : "default"} 
              onClick={() => setActiveFilter(currentUser.department)} 
              clickable 
            />
          )}
        </Box>
      </Box>

      {isLoading && <CircularProgress />}
      {isError && <Typography color="error">Failed to load notices.</Typography>}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {filteredNotices?.map((notice) => (
          <Card key={notice.id} variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="h6">{notice.title}</Typography>
                <Chip label={notice.department.replace('_', ' ').toUpperCase()} size="small" color="primary" variant="outlined" />
              </Box>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>{notice.content}</Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2, pt: 2, borderTop: '1px solid #eee' }}>
                <Typography variant="caption" color="text.secondary">
                  Posted by: <strong>{notice.owner.username}</strong> | {new Date(notice.created_at).toLocaleDateString()}
                </Typography>
                {currentUser?.id === notice.owner_id && (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button size="small" variant="outlined" onClick={() => setEditingNotice(notice)}>Edit</Button>
                    <Button size="small" color="error" onClick={() => deleteMutation.mutate(notice.id)}>Delete</Button>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        ))}
        {filteredNotices?.length === 0 && <Typography>No notices match this filter.</Typography>}
      </Box>

      {editingNotice && (
        <EditNoticeDialog 
          notice={editingNotice} 
          currentUser={currentUser}
          onClose={() => setEditingNotice(null)} 
        />
      )}
    </Box>
  );
}