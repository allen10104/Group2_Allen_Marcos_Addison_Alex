import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { TextField, Button, Box, MenuItem, Paper } from "@mui/material";
import api from "../../api/axios";

// Accept currentUser as a prop
export default function CreateNoticeForm({ currentUser }) {
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const mutation = useMutation({
    mutationFn: async (newNotice) => {
      const response = await api.post("/notices/", newNotice);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notices"] });
      reset();
    },
  });

  const onSubmit = (data) => mutation.mutate(data);

  // If currentUser hasn't loaded yet, don't crash
  if (!currentUser) return null;

  return (
    <Paper sx={{ p: 3 }} variant="outlined">
      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField label="Title" size="small" {...register("title", { required: "Title required" })} error={!!errors.title} />
        <TextField label="Message" multiline rows={3} {...register("content", { required: "Message required" })} error={!!errors.content} />
        
        <TextField select label="Department" defaultValue="all_employees" size="small" {...register("department")}>
          <MenuItem value="all_employees">All Employees</MenuItem>
          {/* Dynamically render the user's specific department */}
          {currentUser.department !== "all_employees" && (
            <MenuItem value={currentUser.department}>
              {currentUser.department.replace('_', ' ').toUpperCase()}
            </MenuItem>
          )}
        </TextField>

        <Button type="submit" variant="contained" disabled={mutation.isPending} sx={{ alignSelf: 'flex-start' }}>
          Post Notice
        </Button>
      </Box>
    </Paper>
  );
}