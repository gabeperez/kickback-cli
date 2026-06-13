# Homebrew formula for kickback.
#
# Tap install (after you push this to github.com/gabeperez/homebrew-kickback):
#   brew install gabeperez/kickback/kickback
#
# `url`/`sha256` point at a GitHub release tarball produced by ./release.sh.
class Kickback < Formula
  desc "Terminal companion for the Kickbacks.ai editor extension (status, earnings, ad history)"
  homepage "https://gabeperez.github.io/kickback-cli"
  url "https://github.com/gabeperez/kickback-cli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "78e8c4ff677f832e5e1227266f3de14623ca06bb4a6c736bf3b84c05f2c4ff6a"
  license "MIT"
  version "0.1.0"

  depends_on "python@3.12" => :recommended  # uses stdlib + openssl; cryptography optional
  depends_on :macos

  def install
    bin.install "kickback"
  end

  def caveats
    <<~EOS
      kickback is safe by default — every feature that writes anything
      (sampler, notifications, token refresh) is OFF until you enable it.

      First run:   kickback init      (writes ~/.config/kickback/config.json)
      Learn more:  kickback about     (what it reads/sends + what could break)
      Live check:  kickback doctor
    EOS
  end

  test do
    assert_match "kickback #{version}", shell_output("#{bin}/kickback --version")
  end
end
