import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2 } from "lucide-react";

import { signUp, signInWithGoogle } from "../services/auth.service";

import AuthLayout from "../layouts/AuthLayout";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();

    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    const { error } = await signUp({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    navigate("/");
  };

  const handleGoogleSignUp = async () => {
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
            Create your account
          </h1>

          <p className="mt-3 max-w-md text-slate-500">
            Join ScholarAI and start discovering government
            schemes tailored to you.
          </p>
        </div>

        <div className="mt-8">
          <Button
            variant="secondary"
            fullWidth
            type="button"
            onClick={handleGoogleSignUp}
          >
            Continue with Google
          </Button>
        </div>

        <div className="my-8 flex items-center gap-4">
          <div className="h-px flex-1 bg-slate-200" />

          <span className="text-sm text-slate-400">
            OR
          </span>

          <div className="h-px flex-1 bg-slate-200" />
        </div>

        <form
          onSubmit={handleRegister}
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

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) =>
              setConfirmPassword(e.target.value)
            }
            required
          />

          {error && (
            <p className="text-sm text-center text-red-500">
              {error}
            </p>
          )}

          <Button
            type="submit"
            fullWidth
            disabled={loading}
          >
            {loading
              ? "Creating Account..."
              : "Create Account"}
          </Button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link
            to="/"
            className="font-semibold text-blue-600 hover:underline"
          >
            Sign In
          </Link>
        </div>
      </Card>
    </AuthLayout>
  );
}