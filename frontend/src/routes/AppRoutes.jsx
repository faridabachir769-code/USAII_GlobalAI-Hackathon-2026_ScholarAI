import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";

import Login from "../pages/Login";
import Register from "../pages/Register";
import ProfileSetup from "../pages/ProfileSetup";
import Dashboard from "../pages/Dashboard";
import Comparison from "../pages/Comparison";
import DecisionReport from "../pages/DecisionReport";
import WhatIfSimulator from "../pages/WhatIfSimulator";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Login />,
  },
  {
    path: "/register",
    element: <Register />,
  },
  {
    path: "/profile",
    element: <ProfileSetup />,
  },
  {
    path: "/dashboard",
    element: <Dashboard />,
  },
  {
    path: "/comparison",
    element: <Comparison />,
  },
  {
    path: "/report",
    element: <DecisionReport />,
  },
  {
    path: "/simulator",
    element: <WhatIfSimulator />,
  },
]);

export default function AppRoutes() {
  return <RouterProvider router={router} />;
}