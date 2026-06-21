import { useState } from "react";
import { useLocation } from "react-router-dom";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import PageHeader from "../components/ui/PageHeader";
import Loader from "../components/ui/Loader";

import { simulateScenario } from "../services/simulation.service";

export default function WhatIfSimulator() {
  const { state } = useLocation();

  const scheme = state?.scheme;

  const [form, setForm] = useState({
    annual_income: "",
    education_level: "",
    category: "",
    age: "",
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  function handleChange(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();

    setLoading(true);

    try {
      const response = await simulateScenario({
        scheme_id: scheme?.id,
        ...form,
      });

      setResult(response.data);
    } catch (error) {
      console.error(error);
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <PageHeader
          title="What-If Simulator"
          subtitle="See how profile changes affect your eligibility."
        />

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <form
              onSubmit={handleSubmit}
              className="space-y-5"
            >
              <Input
                label="Annual Income"
                name="annual_income"
                type="number"
                value={form.annual_income}
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

              <Button
                type="submit"
                fullWidth
                disabled={loading}
              >
                {loading
                  ? "Simulating..."
                  : "Run Simulation"}
              </Button>
            </form>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-bold">
              AI Simulation Result
            </h2>

            {loading && (
              <div className="mt-10 flex justify-center">
                <Loader text="Running simulation..." />
              </div>
            )}

            {!loading && !result && (
              <div className="mt-10 rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                Run a simulation to see the predicted
                outcome.
              </div>
            )}

            {!loading && result && (
              <div className="mt-6 space-y-5">
                <div>
                  <h3 className="font-semibold">
                    Match Score
                  </h3>

                  <p className="mt-2 text-4xl font-bold text-green-600">
                    {result.match_score}%
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold">
                    AI Explanation
                  </h3>

                  <p className="mt-2 leading-7 text-slate-600">
                    {result.explanation}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold">
                    Recommendation
                  </h3>

                  <p className="mt-2 leading-7 text-slate-600">
                    {result.recommendation}
                  </p>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </main>