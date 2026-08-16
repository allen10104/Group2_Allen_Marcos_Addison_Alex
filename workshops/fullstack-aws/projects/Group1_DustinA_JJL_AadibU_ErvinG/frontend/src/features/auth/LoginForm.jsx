import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { TextField, Button, Box, Typography, Alert } from "@mui/material";
import api from "../../api/axios";

export default function LoginForm({ setAuth }) {
  const { register, handleSubmit, formState: { errors } } = useForm();

  const mutation = useMutation({
    mutationFn: async (credentials) => {
      // FastAPI requires form-urlencoded data for the login endpoint
      const formData = new URLSearchParams();
      formData.append("username", credentials.username);
      formData.append("password", credentials.password);
      
      const response = await api.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem("token", data.access_token);
      setAuth(true);
    },
  });

  const onSubmit = (data) => mutation.mutate(data);

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 300, margin: '0 auto', mt: 10 }}>
      <Typography variant="h4" align="center">Sign In</Typography>
      
      {mutation.isError && <Alert severity="error">Invalid username or password</Alert>}

      <TextField
        label="Username"
        {...register("username", { required: "Username is required" })}
        error={!!errors.username}
        helperText={errors.username?.message}
      />
      <TextField
        label="Password"
        type="password"
        {...register("password", { required: "Password is required" })}
        error={!!errors.password}
        helperText={errors.password?.message}
      />
      <Button type="submit" variant="contained" disabled={mutation.isPending}>
        {mutation.isPending ? "Logging in..." : "Login"}
      </Button>
    </Box>
  );
}