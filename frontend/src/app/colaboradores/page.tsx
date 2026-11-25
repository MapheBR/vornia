import { EmployeeManager } from "@/components/employees/employee-manager";
import { LogoutButton } from "@/components/auth/logout-button";

export default function ColaboradoresPage() {
  return (
    <main className="mx-auto max-w-6xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Colaboradores</h1>
        <LogoutButton />
      </div>
      <EmployeeManager />
    </main>
  );
}
