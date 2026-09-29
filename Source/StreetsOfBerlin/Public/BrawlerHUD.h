#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "BrawlerHUD.generated.h"

class ABrawlerFighter;
class UTexture2D;

/** Canvas-HUD im SoR-Stil: Portrait + Energiebalken, Gegnerbalken, Combo-Zaehler, GO-Pfeil, Menues. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

private:
	// Virtuelle Aufloesung 1600x900, wird auf den Bildschirm skaliert
	float S = 1.f;
	float OX = 0.f;
	float OY = 0.f;

	void Rect(float X, float Y, float W, float H, const FLinearColor& Color);
	void Text(const FString& Str, float X, float Y, float Scale, const FLinearColor& Color, bool bCenter = false, bool bRight = false);
	void Tex(UTexture2D* Texture, float X, float Y, float W, float H, float Alpha = 1.f);
	void Bar(float X, float Y, float W, float H, float Value, float Recoverable, const FLinearColor& Color, bool bRightToLeft);
	void FighterPanel(ABrawlerFighter* Fighter, bool bRightSide, float Recoverable);
};
