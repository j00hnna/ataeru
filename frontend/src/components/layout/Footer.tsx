export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} Ataeru. جميع الحقوق محفوظة.
          </p>
          <p className="text-sm text-gray-400 mt-2 sm:mt-0">
            حيث تُمنح الصفقات
          </p>
        </div>
      </div>
    </footer>
  );
}