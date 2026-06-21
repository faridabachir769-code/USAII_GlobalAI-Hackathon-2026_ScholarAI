import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2 } from "lucide-react";

import { signIn, signInWithGoogle } from "../services/auth.service";

import AuthLayout from "../layouts/AuthLayout";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");

    const { error } = await signIn({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    navigate("/profile");
  };

  const handleGoogleLogin = async () => {
    await signInWithGoogle();
  };

  return (
    <AuthLayout>
      <Card className="p-6 md:p-10">
        <div className="flex flex-col items-center text-center">
          <div className="mb-5 rounded-full bg-blue-100 p-4">
            <Building2
              size={36}
              className="text-blue-600"
            />
          </div>

          <h1 className="text-3xl font-bold text-slate-900">
            Welcome Back
          </h1>

          <p className="mt-3 max-w-md text-slate-500">
            Sign in to continue exploring personalized
            government schemes.
          </p>
        </div>

        <div className="mt-8">
          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={handleGoogleLogin}
          >
            Continue with Google
          </Button>
        </div>

        <div className="my-8 flex items-center gap-4">
          <div className="h-px flex-1 bg-slate-200" />
          <span className="text-sm text-slate-400">OR</span>
          <div className="h-px flex-1 bg-slate-200" />
        </div>

        <form
          onSubmit={handleLogin}
          className="space-y-5"
        >
          <Input
            label="Email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            required
          />

          <div className="flex justify-end">
            <button
              type="button"
              className="text-sm text-blue-600 hover:underline"
            >
              Forgot Password?
            </button>
          </div>

          {error && (
            <p className="text-center text-sm text-red-500">
              {error}
            </p>
          )}

          <Button
            type="submit"
            fullWidth
            disabled={loading}
          >
            {loading
              ? "Signing In..."
              : "Sign In"}
          </Button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-500">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-blue-600 hover:underline"
          >
            Create Account
          </Link>
        </div>
      </Card>
    </AuthLayout>
  );
}