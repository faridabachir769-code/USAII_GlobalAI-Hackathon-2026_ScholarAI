import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import AuthLayout from "../layouts/AuthLayout";

import { createProfile } from "../services/profile.service";

export default function ProfileSetup() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    full_name: "",
    age: "",
    gender: "",
    state: "",
    occupation: "",
    education_level: "",
    annual_income: "",
    category: "",
    disability: "no",
  });

  function handleChange(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();

    setLoading(true);
    setError("");

    try {
      await createProfile(form);

      navigate("/dashboard");
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Failed to save profile."
      );
    }

    setLoading(false);
  }

  return (
    <AuthLayout>
      <Card className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Complete Your Profile
          </h1>

          <p className="mt-2 text-slate-500">
            We use this information to personalize
            government scheme recommendations.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          <div className="grid gap-5 md:grid-cols-2">
            <Input
              label="Full Name"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
            />

            <Input
              label="Age"
              name="age"
              type="number"
              value={form.age}
              onChange={handleChange}
            />

            <Select
              label="Gender"
              name="gender"
              value={form.gender}
              onChange={handleChange}
              options={[
                {
                  value: "",
                  label: "Select",
                },
                {
                  value: "male",
                  label: "Male",
                },
                {
                  value: "female",
                  label: "Female",
                },
                {
                  value: "other",
                  label: "Other",
                },
              ]}
            />

            <Input
              label="State"
              name="state"
              value={form.state}
              onChange={handleChange}
            />

            <Input
              label="Occupation"
              name="occupation"
              value={form.occupation}
              onChange={handleChange}
            />

            <Select
              label="Education Level"
              name="education_level"
              value={form.education_level}
              onChange={handleChange}
              options={[
                {
                  value: "",
                  label: "Select",
                },
                {
                  value: "high_school",
                  label: "High School",
                },
                {
                  value: "undergraduate",
                  label: "Undergraduate",
                },
                {
                  value: "masters",
                  label: "Masters",
                },
                {
                  value: "phd",
                  label: "PhD",
                },
              ]}
            />

            <Input
              label="Annual Income"
              name="annual_income"
              type="number"
              value={form.annual_income}
              onChange={handleChange}
            />

            <Select
              label="Category"
              name="category"
              value={form.category}
              onChange={handleChange}
              options={[
                {
                  value: "",
                  label: "Select",
                },
                {
                  value: "general",
                  label: "General",
                },
                {
                  value: "obc",
                  label: "OBC",
                },
                {
                  value: "sc",
                  label: "SC",
                },
                {
                  value: "st",
                  label: "ST",
                },
                {
                  value: "ews",
                  label: "EWS",
                },
              ]}
            />

            <Select
              label="Disability"
              name="disability"
              value={form.disability}
              onChange={handleChange}
              options={[
                {
                  value: "no",
                  label: "No",
                },
                {
                  value: "yes",
                  label: "Yes",
                },
              ]}
            />
          </div>

          {error && (
            <p className="text-sm text-red-500">
              {error}
            </p>
          )}

          <Button
            type="submit"
            fullWidth
            disabled={loading}
          >
            {loading
              ? "Saving..."
              : "Continue to Dashboard"}
          </Button>
        </form>
      </Card>
    </AuthLayout>
  );
}