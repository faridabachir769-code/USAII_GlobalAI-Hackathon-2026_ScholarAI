import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Save } from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import AuthLayout from "../layouts/AuthLayout";
import DashboardLayout from "../layouts/DashboardLayout";
import { createProfile, getProfile, updateProfile } from "../services/profile.service";
import { bumpProfileVersion } from "../hooks/useSchemes";

export default function ProfileSetup() {
  const navigate = useNavigate();
  const isEditing = window.location.pathname === "/profile";

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEditing);
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

  useEffect(() => {
    if (isEditing) {
      getProfile()
        .then((data) => {
          const p = data?.profile || data || {};
          setForm({
            full_name: p.full_name || "",
            age: p.age || "",
            gender: p.gender || "",
            state: p.state || "",
            occupation: p.occupation || "",
            education_level: p.education_level || "",
            annual_income: p.annual_income || "",
            category: p.category || "",
            disability: p.disability || "no",
          });
        })
        .catch(() => {})
        .finally(() => setFetching(false));
    }
  }, [isEditing]);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (isEditing) {
        await updateProfile(form);
      } else {
        await createProfile(form);
      }
      bumpProfileVersion();
      navigate(isEditing ? "/dashboard" : "/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save profile.");
    }
    setLoading(false);
  }

  const content = (
    <Card className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">
          {isEditing ? "Edit Profile" : "Complete Your Profile"}
        </h1>
        <p className="mt-2 text-slate-500">
          {isEditing
            ? "Update your details for better scheme recommendations."
            : "We use this information to personalize government scheme recommendations."}
        </p>
      </div>

      {fetching ? (
        <div className="flex justify-center py-10">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-5 md:grid-cols-2">
            <Input label="Full Name" name="full_name" value={form.full_name} onChange={handleChange} />
            <Input label="Age" name="age" type="number" value={form.age} onChange={handleChange} />
            <Select label="Gender" name="gender" value={form.gender} onChange={handleChange}
              options={[{ value: "", label: "Select" }, { value: "male", label: "Male" }, { value: "female", label: "Female" }, { value: "other", label: "Other" }]}
            />
            <Select label="State / UT" name="state" value={form.state} onChange={handleChange}
              options={[
                { value: "", label: "Select State / UT" },
                { value: "Andhra Pradesh", label: "Andhra Pradesh" },
                { value: "Arunachal Pradesh", label: "Arunachal Pradesh" },
                { value: "Assam", label: "Assam" },
                { value: "Bihar", label: "Bihar" },
                { value: "Chhattisgarh", label: "Chhattisgarh" },
                { value: "Goa", label: "Goa" },
                { value: "Gujarat", label: "Gujarat" },
                { value: "Haryana", label: "Haryana" },
                { value: "Himachal Pradesh", label: "Himachal Pradesh" },
                { value: "Jharkhand", label: "Jharkhand" },
                { value: "Karnataka", label: "Karnataka" },
                { value: "Kerala", label: "Kerala" },
                { value: "Madhya Pradesh", label: "Madhya Pradesh" },
                { value: "Maharashtra", label: "Maharashtra" },
                { value: "Manipur", label: "Manipur" },
                { value: "Meghalaya", label: "Meghalaya" },
                { value: "Mizoram", label: "Mizoram" },
                { value: "Nagaland", label: "Nagaland" },
                { value: "Odisha", label: "Odisha" },
                { value: "Punjab", label: "Punjab" },
                { value: "Rajasthan", label: "Rajasthan" },
                { value: "Sikkim", label: "Sikkim" },
                { value: "Tamil Nadu", label: "Tamil Nadu" },
                { value: "Telangana", label: "Telangana" },
                { value: "Tripura", label: "Tripura" },
                { value: "Uttar Pradesh", label: "Uttar Pradesh" },
                { value: "Uttarakhand", label: "Uttarakhand" },
                { value: "West Bengal", label: "West Bengal" },
                { value: "Andaman and Nicobar Islands", label: "Andaman and Nicobar Islands (UT)" },
                { value: "Chandigarh", label: "Chandigarh (UT)" },
                { value: "Dadra and Nagar Haveli and Daman and Diu", label: "Dadra & Nagar Haveli and Daman & Diu (UT)" },
                { value: "Delhi", label: "Delhi (UT)" },
                { value: "Jammu and Kashmir", label: "Jammu and Kashmir (UT)" },
                { value: "Ladakh", label: "Ladakh (UT)" },
                { value: "Lakshadweep", label: "Lakshadweep (UT)" },
                { value: "Puducherry", label: "Puducherry (UT)" },
                { value: "National", label: "National (All India)" },
              ]}
            />
            <Input label="Occupation" name="occupation" value={form.occupation} onChange={handleChange} placeholder="e.g. Student" />
            <Select label="Education Level" name="education_level" value={form.education_level} onChange={handleChange}
              options={[{ value: "", label: "Select" }, { value: "School", label: "School (10th)" }, { value: "HigherSecondary", label: "Higher Secondary (12th)" }, { value: "Graduate", label: "Graduate" }, { value: "Postgraduate", label: "Postgraduate" }, { value: "PhD", label: "PhD" }, { value: "Diploma", label: "Diploma" }]}
            />
            <Input label="Annual Income (INR)" name="annual_income" type="number" value={form.annual_income} onChange={handleChange} placeholder="e.g. 250000" />
            <Select label="Category" name="category" value={form.category} onChange={handleChange}
              options={[{ value: "", label: "Select" }, { value: "General", label: "General" }, { value: "OBC", label: "OBC" }, { value: "SC", label: "SC" }, { value: "ST", label: "ST" }, { value: "EWS", label: "EWS" }]}
            />
            <Select label="Disability" name="disability" value={form.disability} onChange={handleChange}
              options={[{ value: "no", label: "No" }, { value: "yes", label: "Yes" }]}
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3">
            {isEditing && (
              <Button type="button" variant="secondary" onClick={() => navigate("/dashboard")}>
                <ArrowLeft size={18} />
                Cancel
              </Button>
            )}
            <Button type="submit" fullWidth={!isEditing} disabled={loading}>
              <Save size={18} />
              {loading ? "Saving..." : isEditing ? "Save Changes" : "Continue to Dashboard"}
            </Button>
          </div>
        </form>
      )}
    </Card>
  );

  return isEditing ? <DashboardLayout><main><div className="mx-auto max-w-3xl px-6 py-8">{content}</div></main></DashboardLayout> : <AuthLayout>{content}</AuthLayout>;
}
